from collections import Counter

from text.vietnamese import (
    DEFAULT_ALIGNMENT_SILENCE_LABELS,
    DEFAULT_PAUSE_PHONE,
    SILENCE_IPA_TOKENS,
    VIETNAMESE_IPA_TOKENS,
)


DEFAULT_ALLOWED_PHONES = set(VIETNAMESE_IPA_TOKENS) | set(SILENCE_IPA_TOKENS)


def build_alignment_settings(config=None):
    alignment_config = {}
    if config is not None:
        alignment_config = config.get("preprocessing", {}).get("alignment", {})
    return {
        "pause_phone": alignment_config.get("pause_phone", DEFAULT_PAUSE_PHONE),
        "silence_labels": {
            label.strip()
            for label in alignment_config.get(
                "silence_labels", DEFAULT_ALIGNMENT_SILENCE_LABELS
            )
        },
        "repair_zero_durations": alignment_config.get(
            "repair_zero_durations", True
        ),
        "drop_unrecoverable_zero_durations": alignment_config.get(
            "drop_unrecoverable_zero_durations", True
        ),
        "collapse_consecutive_pauses": alignment_config.get(
            "collapse_consecutive_pauses", True
        ),
        "quality": {
            "min_total_duration_frames": alignment_config.get(
                "min_total_duration_frames", 24
            ),
            "max_zero_duration_repaired": alignment_config.get(
                "max_zero_duration_repaired", 3
            ),
            "max_zero_duration_repaired_ratio": alignment_config.get(
                "max_zero_duration_repaired_ratio", 0.04
            ),
            "max_one_frame_non_silence_count": alignment_config.get(
                "max_one_frame_non_silence_count", 18
            ),
            "max_one_frame_non_silence_ratio": alignment_config.get(
                "max_one_frame_non_silence_ratio", 0.18
            ),
            "max_pause_frame_ratio": alignment_config.get(
                "max_pause_frame_ratio", 0.35
            ),
        },
    }


def normalize_phone_label(phone, pause_phone=DEFAULT_PAUSE_PHONE):
    phone = (phone or "").strip()
    if phone == "":
        return pause_phone
    return phone


def is_silence_phone(phone, settings):
    return phone in settings["silence_labels"] or phone == settings["pause_phone"]


def make_interval(start, end, phone, duration):
    return {
        "start": float(start),
        "end": float(end),
        "phone": phone,
        "duration": int(duration),
    }


def append_example(report, key, payload, limit=10):
    examples = report.setdefault("examples", {}).setdefault(key, [])
    if len(examples) < limit:
        examples.append(payload)


def analyze_alignment_intervals(intervals, settings, allowed_phones=None):
    allowed_phones = DEFAULT_ALLOWED_PHONES if allowed_phones is None else allowed_phones
    report = {"counts": Counter(), "examples": {}, "normalized_intervals": []}
    previous_end = None

    for idx, entry in enumerate(intervals):
        raw_phone = (entry.get("phone") or "").strip()
        phone = normalize_phone_label(raw_phone, settings["pause_phone"])
        duration = int(entry["duration"])
        start = float(entry["start"])
        end = float(entry["end"])

        normalized = {
            "raw_phone": raw_phone,
            "phone": phone,
            "duration": duration,
            "start": start,
            "end": end,
        }
        report["normalized_intervals"].append(normalized)
        report["counts"]["intervals"] += 1

        if raw_phone == "":
            report["counts"]["empty_phone"] += 1
            append_example(
                report,
                "empty_phone",
                {"index": idx, "start": start, "end": end},
            )

        if duration < 0 or end < start:
            report["counts"]["negative_duration"] += 1
            append_example(
                report,
                "negative_duration",
                {"index": idx, "phone": raw_phone, "start": start, "end": end},
            )
        elif duration == 0:
            report["counts"]["zero_duration"] += 1
            append_example(
                report,
                "zero_duration",
                {"index": idx, "phone": phone, "start": start, "end": end},
            )

        if previous_end is not None and start < previous_end:
            report["counts"]["overlap"] += 1
            append_example(
                report,
                "overlap",
                {"index": idx, "phone": phone, "start": start, "previous_end": previous_end},
            )
        previous_end = end

        if phone not in allowed_phones and not is_silence_phone(phone, settings):
            report["counts"]["oov_phone"] += 1
            append_example(
                report,
                "oov_phone",
                {"index": idx, "phone": phone},
            )

    report["counts"] = dict(report["counts"])
    return report


def find_duration_donor(intervals, idx):
    for offset in range(1, len(intervals)):
        left = idx - offset
        if left >= 0 and intervals[left]["duration"] > 1:
            return left

        right = idx + offset
        if right < len(intervals) and intervals[right]["duration"] > 1:
            return right

    return None


def merge_consecutive_pauses(intervals, settings, counters):
    if not intervals:
        return intervals

    merged = [dict(intervals[0])]
    for entry in intervals[1:]:
        if is_silence_phone(entry["phone"], settings) and is_silence_phone(
            merged[-1]["phone"], settings
        ):
            merged[-1]["end"] = entry["end"]
            merged[-1]["duration"] += entry["duration"]
            counters["pause_intervals_merged"] += 1
            continue
        merged.append(dict(entry))

    return merged


def sanitize_alignment_intervals(intervals, settings, allowed_phones=None):
    analysis = analyze_alignment_intervals(intervals, settings, allowed_phones)
    normalized_intervals = [dict(entry) for entry in analysis["normalized_intervals"]]
    repaired_counts = Counter()
    dropped_counts = Counter()
    fatal_errors = []

    if analysis["counts"].get("empty_phone", 0):
        repaired_counts["empty_phone_normalized"] = analysis["counts"]["empty_phone"]

    if analysis["counts"].get("negative_duration", 0):
        fatal_errors.append("negative_duration")
    if analysis["counts"].get("overlap", 0):
        fatal_errors.append("overlap")
    if analysis["counts"].get("oov_phone", 0):
        fatal_errors.append("oov_phone")

    while normalized_intervals and is_silence_phone(normalized_intervals[0]["phone"], settings):
        normalized_intervals.pop(0)
        repaired_counts["leading_silence_trimmed"] += 1
    while normalized_intervals and is_silence_phone(normalized_intervals[-1]["phone"], settings):
        normalized_intervals.pop()
        repaired_counts["trailing_silence_trimmed"] += 1

    if not normalized_intervals:
        fatal_errors.append("empty_after_trim")

    sanitized = []
    for idx, entry in enumerate(normalized_intervals):
        if entry["duration"] > 0:
            sanitized.append(entry)
            continue

        if not settings["repair_zero_durations"]:
            sanitized.append(entry)
            continue

        if is_silence_phone(entry["phone"], settings):
            dropped_counts["zero_duration_pause_dropped"] += 1
            continue

        donor_idx = find_duration_donor(normalized_intervals, idx)
        if donor_idx is not None:
            normalized_intervals[donor_idx]["duration"] -= 1
            entry["duration"] = 1
            repaired_counts["zero_duration_repaired"] += 1
            sanitized.append(entry)
            continue

        dropped_counts["zero_duration_unrecoverable"] += 1
        if not settings["drop_unrecoverable_zero_durations"]:
            sanitized.append(entry)

    if settings["collapse_consecutive_pauses"]:
        sanitized = merge_consecutive_pauses(sanitized, settings, repaired_counts)

    if not sanitized:
        fatal_errors.append("empty_after_repair")

    result = {
        "intervals": [
            make_interval(
                entry["start"],
                entry["end"],
                entry["phone"],
                entry["duration"],
            )
            for entry in sanitized
        ],
        "detected_counts": analysis["counts"],
        "repaired_counts": dict(repaired_counts),
        "dropped_counts": dict(dropped_counts),
        "fatal_errors": fatal_errors,
        "examples": analysis["examples"],
        "valid": len(fatal_errors) == 0,
    }
    return result


def summarize_sanitized_alignment(intervals, settings):
    metrics = {
        "phone_count": len(intervals),
        "total_duration_frames": 0,
        "pause_count": 0,
        "pause_duration_frames": 0,
        "one_frame_non_silence_count": 0,
        "average_frames_per_phone": 0.0,
        "pause_frame_ratio": 0.0,
        "one_frame_non_silence_ratio": 0.0,
    }
    examples = {}

    if not intervals:
        return metrics, examples

    total_duration = 0
    pause_duration = 0
    one_frame_examples = []
    for idx, entry in enumerate(intervals):
        duration = int(entry["duration"])
        phone = entry["phone"]
        total_duration += duration

        if is_silence_phone(phone, settings):
            metrics["pause_count"] += 1
            pause_duration += duration
            continue

        if duration == 1:
            metrics["one_frame_non_silence_count"] += 1
            if len(one_frame_examples) < 10:
                one_frame_examples.append(
                    {
                        "index": idx,
                        "phone": phone,
                        "duration": duration,
                        "start": float(entry["start"]),
                        "end": float(entry["end"]),
                    }
                )

    metrics["total_duration_frames"] = total_duration
    metrics["pause_duration_frames"] = pause_duration
    metrics["average_frames_per_phone"] = total_duration / max(1, len(intervals))
    metrics["pause_frame_ratio"] = pause_duration / max(1, total_duration)
    non_silence_count = max(1, len(intervals) - metrics["pause_count"])
    metrics["one_frame_non_silence_ratio"] = (
        metrics["one_frame_non_silence_count"] / non_silence_count
    )

    if one_frame_examples:
        examples["one_frame_non_silence"] = one_frame_examples

    return metrics, examples


def assess_alignment_quality(alignment_result, settings):
    intervals = alignment_result.get("intervals", [])
    quality_settings = settings.get("quality", {})
    metrics, examples = summarize_sanitized_alignment(intervals, settings)

    quality_issues = []
    detected_counts = Counter()
    drop_reason = None

    min_total_duration_frames = quality_settings.get("min_total_duration_frames", 0)
    if metrics["total_duration_frames"] < min_total_duration_frames:
        detected_counts["too_short_frames"] += 1
        quality_issues.append("too_short_frames")
        drop_reason = drop_reason or "too_short_frames"

    repaired_zero_count = alignment_result.get("repaired_counts", {}).get(
        "zero_duration_repaired", 0
    )
    phone_count = max(1, metrics["phone_count"])
    repaired_zero_ratio = repaired_zero_count / phone_count
    if repaired_zero_count > quality_settings.get("max_zero_duration_repaired", 999999):
        detected_counts["excessive_zero_duration_repaired"] += repaired_zero_count
        quality_issues.append("excessive_zero_duration_repaired")
        drop_reason = drop_reason or "excessive_zero_duration_repaired"
    if repaired_zero_ratio > quality_settings.get("max_zero_duration_repaired_ratio", 1.0):
        detected_counts["high_zero_duration_repaired_ratio"] += 1
        quality_issues.append("high_zero_duration_repaired_ratio")
        drop_reason = drop_reason or "high_zero_duration_repaired_ratio"

    if metrics["one_frame_non_silence_count"] > quality_settings.get(
        "max_one_frame_non_silence_count", 999999
    ):
        detected_counts["excessive_one_frame_non_silence"] += metrics[
            "one_frame_non_silence_count"
        ]
        quality_issues.append("excessive_one_frame_non_silence")
        drop_reason = drop_reason or "excessive_one_frame_non_silence"
    if metrics["one_frame_non_silence_ratio"] > quality_settings.get(
        "max_one_frame_non_silence_ratio", 1.0
    ):
        detected_counts["high_one_frame_non_silence_ratio"] += 1
        quality_issues.append("high_one_frame_non_silence_ratio")
        drop_reason = drop_reason or "high_one_frame_non_silence_ratio"

    if metrics["pause_frame_ratio"] > quality_settings.get("max_pause_frame_ratio", 1.0):
        detected_counts["high_pause_frame_ratio"] += 1
        quality_issues.append("high_pause_frame_ratio")
        drop_reason = drop_reason or "high_pause_frame_ratio"

    return {
        "quality_metrics": metrics,
        "quality_detected_counts": dict(detected_counts),
        "quality_issues": quality_issues,
        "quality_examples": examples,
        "drop_reason": drop_reason,
    }
