import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.io import atomic_write_json, utc_timestamp


def load_yaml_config(path):
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader) or {}


def read_split_records(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            basename, speaker, text, raw_text = stripped.split("|", 3)
            records.append(
                {
                    "line": stripped,
                    "basename": basename,
                    "speaker": speaker,
                    "text": text,
                    "raw_text": raw_text,
                }
            )
    return records


def report_index(report):
    indexed = {}
    for sample in report.get("samples", []):
        speaker = sample.get("speaker")
        basename = sample.get("basename")
        if speaker and basename:
            indexed[(speaker, basename)] = sample
    return indexed


def build_thresholds(config):
    clean_config = (
        config.get("preprocessing", {}).get("clean_subset", {})
        if config
        else {}
    )
    return {
        "min_total_duration_frames": int(
            clean_config.get("min_total_duration_frames", 40)
        ),
        "max_zero_duration_repaired": int(
            clean_config.get("max_zero_duration_repaired", 0)
        ),
        "max_one_frame_non_silence_count": int(
            clean_config.get("max_one_frame_non_silence_count", 12)
        ),
        "max_one_frame_non_silence_ratio": float(
            clean_config.get("max_one_frame_non_silence_ratio", 0.12)
        ),
        "max_pause_frame_ratio": float(
            clean_config.get("max_pause_frame_ratio", 0.28)
        ),
        "max_samples_per_split": int(clean_config.get("max_samples_per_split", 0)),
    }


def apply_overrides(thresholds, args):
    overrides = {
        "min_total_duration_frames": args.min_total_duration_frames,
        "max_zero_duration_repaired": args.max_zero_duration_repaired,
        "max_one_frame_non_silence_count": args.max_one_frame_non_silence_count,
        "max_one_frame_non_silence_ratio": args.max_one_frame_non_silence_ratio,
        "max_pause_frame_ratio": args.max_pause_frame_ratio,
        "max_samples_per_split": args.max_samples_per_split,
    }
    for key, value in overrides.items():
        if value is not None:
            thresholds[key] = value
    return thresholds


def score_sample(sample_metrics, repaired_counts):
    zero_duration_repaired = int(repaired_counts.get("zero_duration_repaired", 0))
    total_frames = int(sample_metrics.get("total_duration_frames", 0))
    one_frame_ratio = float(sample_metrics.get("one_frame_non_silence_ratio", 1.0))
    pause_ratio = float(sample_metrics.get("pause_frame_ratio", 1.0))
    one_frame_count = int(sample_metrics.get("one_frame_non_silence_count", 0))
    return (
        zero_duration_repaired,
        round(one_frame_ratio, 6),
        round(pause_ratio, 6),
        one_frame_count,
        -total_frames,
    )


def evaluate_sample(sample, thresholds):
    fatal_errors = sample.get("fatal_errors", [])
    drop_reason = sample.get("drop_reason")
    if fatal_errors:
        return False, "fatal_errors"
    if drop_reason:
        return False, drop_reason

    quality_metrics = sample.get("quality_metrics", {})
    repaired_counts = sample.get("repaired_counts", {})

    if int(quality_metrics.get("total_duration_frames", 0)) < thresholds[
        "min_total_duration_frames"
    ]:
        return False, "too_short_frames"
    if int(repaired_counts.get("zero_duration_repaired", 0)) > thresholds[
        "max_zero_duration_repaired"
    ]:
        return False, "zero_duration_repaired"
    if int(quality_metrics.get("one_frame_non_silence_count", 0)) > thresholds[
        "max_one_frame_non_silence_count"
    ]:
        return False, "one_frame_non_silence_count"
    if float(quality_metrics.get("one_frame_non_silence_ratio", 1.0)) > thresholds[
        "max_one_frame_non_silence_ratio"
    ]:
        return False, "one_frame_non_silence_ratio"
    if float(quality_metrics.get("pause_frame_ratio", 1.0)) > thresholds[
        "max_pause_frame_ratio"
    ]:
        return False, "pause_frame_ratio"

    return True, "kept"


def select_records(records, indexed_report, thresholds):
    kept = []
    dropped_counts = {}
    missing_report_records = []

    for record in records:
        sample = indexed_report.get((record["speaker"], record["basename"]))
        if sample is None:
            dropped_counts["missing_report_record"] = (
                dropped_counts.get("missing_report_record", 0) + 1
            )
            missing_report_records.append(
                {
                    "speaker": record["speaker"],
                    "basename": record["basename"],
                }
            )
            continue

        keep, reason = evaluate_sample(sample, thresholds)
        if not keep:
            dropped_counts[reason] = dropped_counts.get(reason, 0) + 1
            continue

        kept.append(
            {
                "record": record,
                "score": score_sample(
                    sample.get("quality_metrics", {}),
                    sample.get("repaired_counts", {}),
                ),
                "quality_metrics": sample.get("quality_metrics", {}),
                "repaired_counts": sample.get("repaired_counts", {}),
            }
        )

    kept.sort(key=lambda item: item["score"])
    max_samples = int(thresholds.get("max_samples_per_split", 0))
    if max_samples > 0 and len(kept) > max_samples:
        dropped_counts["trimmed_after_ranking"] = len(kept) - max_samples
        kept = kept[:max_samples]

    return kept, dropped_counts, missing_report_records


def write_split(path, kept_records):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for item in kept_records:
            f.write(item["record"]["line"] + "\n")


def summarize_split(name, input_records, kept_records, dropped_counts):
    quality_examples = []
    for item in kept_records[:10]:
        quality_examples.append(
            {
                "speaker": item["record"]["speaker"],
                "basename": item["record"]["basename"],
                "raw_text": item["record"]["raw_text"],
                "quality_metrics": item["quality_metrics"],
                "repaired_counts": item["repaired_counts"],
            }
        )

    return {
        "split": name,
        "input_samples": len(input_records),
        "kept_samples": len(kept_records),
        "dropped_samples": len(input_records) - len(kept_records),
        "dropped_counts": dropped_counts,
        "kept_examples": quality_examples,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="config/InfoRe1_25hours/preprocess.yaml",
        help="Path to preprocess.yaml for clean subset defaults.",
    )
    parser.add_argument(
        "--report-path",
        default="preprocessed_data/InfoRe1/alignment_validation_report.json",
        help="Alignment validation report path.",
    )
    parser.add_argument(
        "--input-train",
        default="preprocessed_data/InfoRe1/train.txt",
        help="Input training split.",
    )
    parser.add_argument(
        "--input-val",
        default="preprocessed_data/InfoRe1/val.txt",
        help="Input validation split.",
    )
    parser.add_argument(
        "--output-train",
        default="preprocessed_data/InfoRe1/train.clean.txt",
        help="Output clean training split.",
    )
    parser.add_argument(
        "--output-val",
        default="preprocessed_data/InfoRe1/val.clean.txt",
        help="Output clean validation split.",
    )
    parser.add_argument(
        "--summary-path",
        default="preprocessed_data/InfoRe1/clean_subset_report.json",
        help="Output summary JSON path.",
    )
    parser.add_argument("--min-total-duration-frames", type=int, default=None)
    parser.add_argument("--max-zero-duration-repaired", type=int, default=None)
    parser.add_argument("--max-one-frame-non-silence-count", type=int, default=None)
    parser.add_argument("--max-one-frame-non-silence-ratio", type=float, default=None)
    parser.add_argument("--max-pause-frame-ratio", type=float, default=None)
    parser.add_argument("--max-samples-per-split", type=int, default=None)
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    thresholds = apply_overrides(build_thresholds(config), args)

    with open(args.report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    indexed_report = report_index(report)

    train_records = read_split_records(args.input_train)
    val_records = read_split_records(args.input_val)

    train_kept, train_dropped, train_missing = select_records(
        train_records, indexed_report, thresholds
    )
    val_kept, val_dropped, val_missing = select_records(
        val_records, indexed_report, thresholds
    )

    output_train = Path(args.output_train)
    output_val = Path(args.output_val)
    output_train.parent.mkdir(parents=True, exist_ok=True)
    output_val.parent.mkdir(parents=True, exist_ok=True)
    write_split(output_train, train_kept)
    write_split(output_val, val_kept)

    summary = {
        "generated_at": utc_timestamp(),
        "report_path": args.report_path,
        "thresholds": thresholds,
        "report_samples_indexed": len(indexed_report),
        "splits": {
            "train": summarize_split("train", train_records, train_kept, train_dropped),
            "val": summarize_split("val", val_records, val_kept, val_dropped),
        },
        "missing_report_records": {
            "train": train_missing[:20],
            "val": val_missing[:20],
        },
    }
    atomic_write_json(summary, args.summary_path)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Saved clean train split to {args.output_train}")
    print(f"Saved clean val split to {args.output_val}")
    print(f"Saved clean subset summary to {args.summary_path}")


if __name__ == "__main__":
    main()
