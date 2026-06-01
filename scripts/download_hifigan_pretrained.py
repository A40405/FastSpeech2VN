import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        default="https://drive.google.com/drive/folders/1DOhZGlTLMbbAAFZmZGDdc77kz1PloS7F?usp=sharing",
        help="Google Drive folder URL that contains pretrained checkpoints.",
    )
    parser.add_argument(
        "--target-dir",
        default="hifigan",
        help="Directory to store HiFi-GAN checkpoints.",
    )
    args = parser.parse_args()

    try:
        import gdown
    except ImportError as exc:
        raise SystemExit(
            "gdown is required. Install with: pip install gdown"
        ) from exc

    target = Path(args.target_dir)
    target.mkdir(parents=True, exist_ok=True)
    tmp_dir = target / "_tmp_pretrained"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    gdown.download_folder(url=args.url, output=str(tmp_dir), quiet=False, use_cookies=False)

    copied = 0
    needed = {
        "generator_LJSpeech.pth.tar",
        "generator_universal.pth.tar",
        "generator_LJSpeech.pth.tar.zip",
        "generator_universal.pth.tar.zip",
    }
    for src in tmp_dir.rglob("*"):
        if src.is_file() and src.name in needed:
            shutil.copy2(src, target / src.name)
            copied += 1

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"Done. Copied {copied} HiFi-GAN files to {target.resolve()}")


if __name__ == "__main__":
    main()
