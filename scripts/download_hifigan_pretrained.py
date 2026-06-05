import argparse
import shutil
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

DIRECT_FILES = {
    "universal": {
        "archive_name": "generator_universal.pth.tar.zip",
        "checkpoint_name": "generator_universal.pth.tar",
        "direct_sources": [
            {
                "kind": "archive",
                "url": "https://github.com/ming024/FastSpeech2/raw/master/hifigan/generator_universal.pth.tar.zip",
                "label": "GitHub raw upstream archive",
            }
        ],
    },
    "ljspeech": {
        "archive_name": "generator_LJSpeech.pth.tar.zip",
        "checkpoint_name": "generator_LJSpeech.pth.tar",
        "direct_sources": [
            {
                "kind": "archive",
                "url": "https://github.com/ming024/FastSpeech2/raw/master/hifigan/generator_LJSpeech.pth.tar.zip",
                "label": "GitHub raw upstream archive",
            }
        ],
    },
}

FOLDER_ALIASES = {
    "generator_universal.pth.tar.zip": {
        "generator_universal.pth.tar.zip",
    },
    "generator_LJSpeech.pth.tar.zip": {
        "generator_LJSpeech.pth.tar.zip",
    },
}

def download_http_file(url, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = destination.with_suffix(destination.suffix + ".part")
    if tmp_path.exists():
        tmp_path.unlink()
    urlretrieve(url, tmp_path)
    tmp_path.replace(destination)
    return destination.exists()


def extract_archive(archive_path, checkpoint_name, target_dir):
    checkpoint_path = target_dir / checkpoint_name
    if checkpoint_path.exists():
        return checkpoint_path

    with zipfile.ZipFile(archive_path, "r") as zf:
        zf.extractall(target_dir)

    if checkpoint_path.exists():
        return checkpoint_path

    extracted = list(target_dir.rglob("*.pth.tar"))
    if len(extracted) == 1:
        extracted[0].replace(checkpoint_path)
        return checkpoint_path

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        default="https://drive.google.com/drive/folders/1DOhZGlTLMbbAAFZmZGDdc77kz1PloS7F?usp=sharing",
        help="Legacy Google Drive folder URL used as a fallback source.",
    )
    parser.add_argument(
        "--target-dir",
        default="hifigan",
        help="Directory to store HiFi-GAN checkpoints.",
    )
    parser.add_argument(
        "--variants",
        nargs="+",
        choices=sorted(DIRECT_FILES.keys()),
        default=["universal"],
        help="HiFi-GAN variants to download. Default matches the InfoRe1 config.",
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

    for variant in args.variants:
        spec = DIRECT_FILES[variant]
        archive_path = target / spec["archive_name"]
        checkpoint_path = target / spec["checkpoint_name"]
        if archive_path.exists() or checkpoint_path.exists():
            continue
        for source in spec["direct_sources"]:
            try:
                if source["kind"] == "checkpoint":
                    if download_http_file(source["url"], checkpoint_path):
                        break
                elif source["kind"] == "archive":
                    if download_http_file(source["url"], archive_path):
                        break
            except Exception as exc:
                print(
                    "Warning: failed to download {} from {}: {}".format(
                        variant, source["label"], exc
                    )
                )

    still_needed = [
        variant
        for variant in args.variants
        if not (target / DIRECT_FILES[variant]["archive_name"]).exists()
        and not (target / DIRECT_FILES[variant]["checkpoint_name"]).exists()
    ]

    if still_needed:
        gdown.download_folder(
            url=args.url, output=str(tmp_dir), quiet=False, use_cookies=False
        )
        for variant in still_needed:
            archive_name = DIRECT_FILES[variant]["archive_name"]
            for src in tmp_dir.rglob("*"):
                if src.is_file() and src.name in FOLDER_ALIASES[archive_name]:
                    shutil.copy2(src, target / archive_name)
                    break

    shutil.rmtree(tmp_dir, ignore_errors=True)

    ready = []
    missing = []
    for variant in args.variants:
        spec = DIRECT_FILES[variant]
        archive_path = target / spec["archive_name"]
        checkpoint_path = target / spec["checkpoint_name"]
        if archive_path.exists():
            extracted = extract_archive(archive_path, spec["checkpoint_name"], target)
            if extracted is not None and extracted.exists():
                ready.append(spec["checkpoint_name"])
                continue
        if checkpoint_path.exists():
            ready.append(spec["checkpoint_name"])
        else:
            missing.append(spec["checkpoint_name"])

    if missing:
        raise SystemExit(
            "Missing required HiFi-GAN checkpoints after download: {}. "
            "The configured public sources did not return the expected files."
            .format(", ".join(missing))
        )

    print(
        "Done. Prepared {} in {}".format(
            ", ".join(sorted(ready)), target.resolve()
        )
    )


if __name__ == "__main__":
    main()
