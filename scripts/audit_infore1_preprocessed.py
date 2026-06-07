import argparse
import json
import os
from collections import Counter

import numpy as np


def iter_split_records(root, split_name):
    split_path = os.path.join(root, split_name)
    with open(split_path, "r", encoding="utf-8") as f:
        for line in f:
            basename, speaker, text, raw_text = line.rstrip("\n").split("|")
            yield basename, speaker, text, raw_text


def load_feature(root, speaker, basename, feature_name):
    filename = f"{speaker}-{feature_name}-{basename}.npy"
    return np.load(os.path.join(root, feature_name, filename))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default="preprocessed_data/InfoRe1",
        help="Preprocessed InfoRe1 root",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional max sample count per split for a quick audit",
    )
    args = parser.parse_args()

    root = args.root
    summary = {
        "splits": {},
        "totals": Counter(),
        "examples": {
            "zero_duration": [],
            "duration_mismatch": [],
            "pitch_mismatch": [],
            "energy_mismatch": [],
        },
    }

    for split_name in ("train.txt", "val.txt"):
        split_counter = Counter()
        for idx, (basename, speaker, text, _) in enumerate(
            iter_split_records(root, split_name)
        ):
            if args.limit and idx >= args.limit:
                break

            duration = load_feature(root, speaker, basename, "duration")
            pitch = load_feature(root, speaker, basename, "pitch")
            energy = load_feature(root, speaker, basename, "energy")
            mel = load_feature(root, speaker, basename, "mel")
            token_count = len(text[1:-1].split())
            mel_frames = int(mel.shape[0])
            dur_sum = int(duration.sum())
            zero_duration = int((duration == 0).sum())

            split_counter["samples"] += 1
            split_counter["phones"] += int(len(duration))
            split_counter["zero_duration_phones"] += zero_duration

            if zero_duration:
                split_counter["samples_with_zero_duration"] += 1
                if len(summary["examples"]["zero_duration"]) < 10:
                    summary["examples"]["zero_duration"].append(
                        {
                            "split": split_name,
                            "basename": basename,
                            "zero_duration": zero_duration,
                        }
                    )

            if dur_sum != mel_frames:
                split_counter["duration_mismatches"] += 1
                if len(summary["examples"]["duration_mismatch"]) < 10:
                    summary["examples"]["duration_mismatch"].append(
                        {
                            "split": split_name,
                            "basename": basename,
                            "duration_sum": dur_sum,
                            "mel_frames": mel_frames,
                        }
                    )

            if len(duration) != token_count:
                split_counter["token_mismatches"] += 1

            if len(pitch) not in (token_count, mel_frames):
                split_counter["pitch_mismatches"] += 1
                if len(summary["examples"]["pitch_mismatch"]) < 10:
                    summary["examples"]["pitch_mismatch"].append(
                        {
                            "split": split_name,
                            "basename": basename,
                            "pitch_len": int(len(pitch)),
                            "token_count": token_count,
                            "mel_frames": mel_frames,
                        }
                    )

            if len(energy) not in (token_count, mel_frames):
                split_counter["energy_mismatches"] += 1
                if len(summary["examples"]["energy_mismatch"]) < 10:
                    summary["examples"]["energy_mismatch"].append(
                        {
                            "split": split_name,
                            "basename": basename,
                            "energy_len": int(len(energy)),
                            "token_count": token_count,
                            "mel_frames": mel_frames,
                        }
                    )

        summary["splits"][split_name] = dict(split_counter)
        summary["totals"].update(split_counter)

    summary["totals"] = dict(summary["totals"])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
