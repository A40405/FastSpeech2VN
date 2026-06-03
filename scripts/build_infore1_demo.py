import argparse
import json
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class DemoSample:
    sample_id: str
    speaker: str
    basename: str
    transcript: str
    ground_truth: str
    synthesized: str


def safe_mkdir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path):
    safe_mkdir(dst.parent)
    shutil.copy2(src, dst)


def read_text_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def find_pairs_from_outputs(raw_root: Path, synth_root: Path) -> List[DemoSample]:
    raw_index = {}
    for wav_path in raw_root.rglob("*.wav"):
        speaker = wav_path.parent.name
        basename = wav_path.stem
        lab_path = wav_path.with_suffix(".lab")
        raw_index[basename] = {
            "speaker": speaker,
            "wav": wav_path,
            "lab": lab_path,
        }

    samples: List[DemoSample] = []
    for synth_path in sorted(synth_root.glob("*.wav")):
        basename = synth_path.stem
        if basename not in raw_index:
            continue
        raw_item = raw_index[basename]
        speaker = raw_item["speaker"]
        sample_id = f"{speaker}__{basename}"
        samples.append(
            DemoSample(
                sample_id=sample_id,
                speaker=speaker,
                basename=basename,
                transcript=read_text_file(raw_item["lab"]),
                ground_truth=str(raw_item["wav"]),
                synthesized=str(synth_path),
            )
        )
    return samples


def find_pairs_from_stage(pair_root: Path) -> List[DemoSample]:
    samples: List[DemoSample] = []
    ground_truth_files = sorted(pair_root.rglob("*_ground-truth.wav"))
    for gt_path in ground_truth_files:
        basename = gt_path.name[: -len("_ground-truth.wav")]
        synth_path = gt_path.with_name(f"{basename}_synthesized.wav")
        if not synth_path.exists():
            continue
        transcript_path = None
        for candidate_name in (f"{basename}.txt", f"{basename}.lab", f"{basename}_text.txt"):
            candidate = gt_path.with_name(candidate_name)
            if candidate.exists():
                transcript_path = candidate
                break
        samples.append(
            DemoSample(
                sample_id=basename,
                speaker=gt_path.parent.name,
                basename=basename,
                transcript=read_text_file(transcript_path) if transcript_path else "",
                ground_truth=str(gt_path),
                synthesized=str(synth_path),
            )
        )
    return samples


def write_manifest(output_root: Path, samples: List[DemoSample]):
    manifest_path = output_root / "manifest.json"
    manifest_path.write_text(
        json.dumps([asdict(sample) for sample in samples], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_index(output_root: Path, samples: List[DemoSample]):
    index_path = output_root / "index.md"
    lines = [
        "# InfoRe1 Demo",
        "",
        "This folder is generated automatically by `scripts/build_infore1_demo.py`.",
        "",
        "## Samples",
        "",
    ]
    if not samples:
        lines.append("No samples were generated yet.")
    else:
        for sample in samples:
            lines.append(f"- `{sample.sample_id}`")
            if sample.transcript:
                lines.append(f"  - transcript: {sample.transcript}")
            lines.append(f"  - ground truth: `samples/{sample.sample_id}/ground-truth.wav`")
            lines.append(f"  - synthesized: `samples/{sample.sample_id}/synthesized.wav`")
            lines.append("")
    index_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_readme(output_root: Path):
    readme_path = output_root / "README.md"
    readme_text = """# InfoRe1 Demo\n\nThis folder is the Vietnamese demo area for the clean repo.\n\n## How it is used\n\n- place or generate paired demo WAV files\n- run `scripts/build_infore1_demo.py`\n- the script will copy the pairs into `samples/` and generate `manifest.json` and `index.md`\n\n## Expected sample layout\n\nGenerated sample folders look like this:\n\n```text\ndemo/InfoRe1/samples/<sample_id>/\n  ground-truth.wav\n  synthesized.wav\n  transcript.txt\n```\n\n## Manual staging layout\n\nIf you want to stage files by hand before building the demo, use this pattern:\n\n```text\ndemo/InfoRe1/inbox/<sample_id>_ground-truth.wav\ndemo/InfoRe1/inbox/<sample_id>_synthesized.wav\ndemo/InfoRe1/inbox/<sample_id>.txt\n```\n\nThen run the build script again.\n"""
    readme_path.write_text(readme_text, encoding="utf-8")


def build_demo(samples: List[DemoSample], output_root: Path):
    samples_root = output_root / "samples"
    safe_mkdir(samples_root)

    copied_samples: List[DemoSample] = []
    for sample in samples:
        sample_dir = samples_root / sample.sample_id
        safe_mkdir(sample_dir)
        gt_dst = sample_dir / "ground-truth.wav"
        synth_dst = sample_dir / "synthesized.wav"
        copy_file(Path(sample.ground_truth), gt_dst)
        copy_file(Path(sample.synthesized), synth_dst)
        transcript_path = sample_dir / "transcript.txt"
        transcript_path.write_text(sample.transcript, encoding="utf-8")
        copied_samples.append(
            DemoSample(
                sample_id=sample.sample_id,
                speaker=sample.speaker,
                basename=sample.basename,
                transcript=sample.transcript,
                ground_truth=str(gt_dst),
                synthesized=str(synth_dst),
            )
        )

    write_manifest(output_root, copied_samples)
    write_index(output_root, copied_samples)
    write_readme(output_root)
    return copied_samples


def main():
    parser = argparse.ArgumentParser(description="Build the Vietnamese demo package for InfoRe1.")
    parser.add_argument("--raw-root", default="raw_data/InfoRe1", help="Prepared raw corpus root")
    parser.add_argument("--synth-root", default="output/result/InfoRe1", help="Directory containing synthesized WAV files")
    parser.add_argument("--pair-root", default=None, help="Optional staged folder with *_ground-truth.wav and *_synthesized.wav pairs")
    parser.add_argument("--output-root", default="demo/InfoRe1", help="Output demo directory")
    parser.add_argument("--max-samples", type=int, default=8, help="Maximum number of samples to export")
    args = parser.parse_args()

    output_root = Path(args.output_root)
    safe_mkdir(output_root)

    if args.pair_root:
        samples = find_pairs_from_stage(Path(args.pair_root))
    else:
        samples = find_pairs_from_outputs(Path(args.raw_root), Path(args.synth_root))

    samples = samples[: args.max_samples]
    copied_samples = build_demo(samples, output_root)

    print(f"Built demo at: {output_root}")
    print(f"Samples exported: {len(copied_samples)}")
    for sample in copied_samples:
        print(f"- {sample.sample_id}")


if __name__ == "__main__":
    main()
