import argparse
from pathlib import Path

import librosa
import tgt

from text.vietnamese import DEFAULT_PAUSE_PHONE


def build_textgrid(tokens, total_duration):
    textgrid = tgt.TextGrid()
    tier = tgt.IntervalTier(name="phones")

    if not tokens:
        tier.add_interval(tgt.Interval(0.0, total_duration, DEFAULT_PAUSE_PHONE))
    else:
        step = total_duration / len(tokens)
        current = 0.0
        for idx, token in enumerate(tokens):
            start = current
            end = total_duration if idx == len(tokens) - 1 else current + step
            tier.add_interval(tgt.Interval(start, end, token))
            current = end

    textgrid.add_tier(tier)
    return textgrid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", default="raw_data/InfoRe1", help="Raw data root")
    parser.add_argument(
        "--output-root",
        default="preprocessed_data/InfoRe1/TextGrid",
        help="TextGrid output root",
    )
    parser.add_argument("--sample-rate", type=int, default=22050)
    args = parser.parse_args()

    raw_root = Path(args.raw_root)
    output_root = Path(args.output_root)

    for speaker_dir in sorted([p for p in raw_root.iterdir() if p.is_dir()]):
        speaker_out = output_root / speaker_dir.name
        speaker_out.mkdir(parents=True, exist_ok=True)

        for wav_path in sorted(speaker_dir.glob("*.wav")):
            lab_path = wav_path.with_suffix(".lab")
            phone_path = wav_path.with_suffix(".phones")
            if not lab_path.exists() or not phone_path.exists():
                continue

            tokens = phone_path.read_text(encoding="utf-8").strip().split()
            wav, sr = librosa.load(wav_path, sr=args.sample_rate)
            duration = max(len(wav) / sr, 1e-3)
            textgrid = build_textgrid(tokens, duration)
            out_path = speaker_out / f"{wav_path.stem}.TextGrid"
            tgt.io.write_to_file(textgrid, str(out_path), format="long")

    print(f"Bootstrapped TextGrids into {output_root}")


if __name__ == "__main__":
    main()
