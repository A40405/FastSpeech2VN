import argparse
import json
import os
import sys
from pathlib import Path

import tgt
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from preprocessor.alignment_utils import (
    build_alignment_settings,
    make_interval,
    sanitize_alignment_intervals,
)
from utils.io import atomic_write_json, utc_timestamp


def iter_textgrid_paths(textgrid_root):
    for speaker in sorted(os.listdir(textgrid_root)):
        speaker_dir = os.path.join(textgrid_root, speaker)
        if not os.path.isdir(speaker_dir):
            continue
        for filename in sorted(os.listdir(speaker_dir)):
            if filename.endswith(".TextGrid"):
                yield speaker, os.path.join(speaker_dir, filename)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="config/InfoRe1_25hours/preprocess.yaml",
        help="Path to preprocess.yaml",
    )
    parser.add_argument(
        "--report-path",
        default="preprocessed_data/InfoRe1/alignment_validation_report.json",
        help="Output JSON report path",
    )
    parser.add_argument(
        "--fail-on-errors",
        action="store_true",
        help="Exit non-zero when any fatal alignment issue is found",
    )
    args = parser.parse_args()

    config = yaml.load(open(args.config, "r", encoding="utf-8"), Loader=yaml.FullLoader)
    settings = build_alignment_settings(config)
    textgrid_root = os.path.join(
        config["path"]["preprocessed_path"],
        "TextGrid",
    )
    sampling_rate = config["preprocessing"]["audio"]["sampling_rate"]
    hop_length = config["preprocessing"]["stft"]["hop_length"]

    report = {
        "generated_at": utc_timestamp(),
        "textgrid_root": textgrid_root,
        "summary": {
            "samples_seen": 0,
            "samples_with_fatal_errors": 0,
            "samples_with_detected_issues": 0,
        },
        "detected_counts": {},
        "repaired_counts": {},
        "dropped_counts": {},
        "fatal_reasons": {},
        "samples": [],
    }

    for speaker, textgrid_path in iter_textgrid_paths(textgrid_root):
        basename = os.path.splitext(os.path.basename(textgrid_path))[0]
        report["summary"]["samples_seen"] += 1
        sample = {
            "speaker": speaker,
            "basename": basename,
            "textgrid_path": textgrid_path,
        }
        try:
            textgrid = tgt.io.read_textgrid(textgrid_path)
            tier = textgrid.get_tier_by_name("phones")
            intervals = []
            for interval in tier._objects:
                start = float(interval.start_time)
                end = float(interval.end_time)
                duration = int(
                    round(end * sampling_rate / hop_length)
                    - round(start * sampling_rate / hop_length)
                )
                intervals.append(make_interval(start, end, interval.text, duration))

            result = sanitize_alignment_intervals(intervals, settings)
            sample["detected_counts"] = result["detected_counts"]
            sample["repaired_counts"] = result["repaired_counts"]
            sample["dropped_counts"] = result["dropped_counts"]
            sample["fatal_errors"] = result["fatal_errors"]
            sample["examples"] = result["examples"]

            if any(result["detected_counts"].values()):
                report["summary"]["samples_with_detected_issues"] += 1
            if result["fatal_errors"]:
                report["summary"]["samples_with_fatal_errors"] += 1
                for reason in result["fatal_errors"]:
                    report["fatal_reasons"][reason] = (
                        report["fatal_reasons"].get(reason, 0) + 1
                    )

            for group_name in ("detected_counts", "repaired_counts", "dropped_counts"):
                for key, value in result[group_name].items():
                    report[group_name][key] = report[group_name].get(key, 0) + int(value)
        except Exception as exc:
            sample["fatal_errors"] = ["alignment_parse_error"]
            sample["error_message"] = str(exc)
            report["summary"]["samples_with_fatal_errors"] += 1
            report["fatal_reasons"]["alignment_parse_error"] = (
                report["fatal_reasons"].get("alignment_parse_error", 0) + 1
            )

        if len(report["samples"]) < 100:
            report["samples"].append(sample)

    atomic_write_json(report, args.report_path)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"Saved alignment validation report to {args.report_path}")

    if args.fail_on_errors and report["summary"]["samples_with_fatal_errors"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
