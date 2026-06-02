import argparse
import csv
import fnmatch
import re
import time
from pathlib import Path

import pyarrow.parquet as pq
import requests
from huggingface_hub import HfApi, hf_hub_url
from tqdm import tqdm


def slugify(value):
    value = re.sub(r"[^0-9A-Za-z_-]+", "_", value)
    return value.strip("_") or "sample"


def is_valid_parquet_file(path):
    if not path.exists() or path.stat().st_size < 8:
        return False
    try:
        with path.open("rb") as f:
            head = f.read(4)
            f.seek(-4, 2)
            tail = f.read(4)
        return head == b"PAR1" and tail == b"PAR1"
    except OSError:
        return False


def remove_with_retry(path, max_retries=6):
    for attempt in range(1, max_retries + 1):
        try:
            if path.exists():
                path.unlink()
            return
        except PermissionError:
            if attempt == max_retries:
                break
            time.sleep(min(10, attempt))

    if path.exists():
        quarantine = path.with_suffix(path.suffix + f".corrupt.{int(time.time())}")
        try:
            path.replace(quarantine)
            print(f"Quarantined locked/corrupt file: {quarantine}")
        except OSError as exc:
            raise RuntimeError(f"Cannot remove or quarantine locked file: {path}") from exc


def download_file(url, destination, max_retries=8):
    destination.parent.mkdir(parents=True, exist_ok=True)
    part_path = destination.with_suffix(destination.suffix + ".part")
    expected_size = None

    try:
        head_resp = requests.head(url, timeout=60, allow_redirects=True)
        head_resp.raise_for_status()
        content_len = head_resp.headers.get("Content-Length")
        if content_len is not None:
            expected_size = int(content_len)
    except requests.exceptions.RequestException:
        expected_size = None

    for attempt in range(1, max_retries + 1):
        try:
            downloaded_size = part_path.stat().st_size if part_path.exists() else 0
            headers = {}
            if downloaded_size > 0:
                headers["Range"] = f"bytes={downloaded_size}-"

            with requests.get(url, stream=True, timeout=300, headers=headers) as response:
                if response.status_code == 416:
                    part_path.replace(destination)
                    return
                response.raise_for_status()
                open_mode = "ab" if downloaded_size > 0 and response.status_code == 206 else "wb"
                if open_mode == "wb" and part_path.exists():
                    part_path.unlink()
                with part_path.open(open_mode) as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)

            final_size = part_path.stat().st_size if part_path.exists() else 0
            if expected_size is not None and final_size < expected_size:
                raise RuntimeError(
                    f"Incomplete file {destination.name}: {final_size}/{expected_size} bytes"
                )
            if final_size > 0:
                part_path.replace(destination)
                return
        except (requests.exceptions.RequestException, OSError) as exc:
            if attempt == max_retries:
                raise RuntimeError(
                    f"Failed downloading {destination.name} after {max_retries} attempts"
                ) from exc
            wait_sec = min(30, 2 * attempt)
            print(
                f"Retry {attempt}/{max_retries} for {destination.name} in {wait_sec}s due to: {exc}"
            )
            time.sleep(wait_sec)


def iter_local_parquets(dataset_id, split, download_dir):
    api = HfApi()
    pattern = f"data/{split}-*.parquet"
    repo_files = api.list_repo_files(dataset_id, repo_type="dataset")
    parquet_files = sorted([f for f in repo_files if fnmatch.fnmatch(f, pattern)])
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files matched {pattern}")

    for parquet_file in parquet_files:
        local_path = download_dir / Path(parquet_file).name
        if not local_path.exists():
            url = hf_hub_url(
                repo_id=dataset_id,
                filename=parquet_file,
                repo_type="dataset",
            )
            download_file(url, local_path)
        elif local_path.stat().st_size == 0:
            remove_with_retry(local_path)
            url = hf_hub_url(
                repo_id=dataset_id,
                filename=parquet_file,
                repo_type="dataset",
            )
            download_file(url, local_path)
        else:
            if not is_valid_parquet_file(local_path):
                remove_with_retry(local_path)
                url = hf_hub_url(
                    repo_id=dataset_id,
                    filename=parquet_file,
                    repo_type="dataset",
                )
                download_file(url, local_path)
        yield local_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        default="doof-ferb/infore1_25hours",
        help="Hugging Face dataset id",
    )
    parser.add_argument("--split", default="train", help="Dataset split prefix")
    parser.add_argument(
        "--output-dir",
        default="corpus/infore1_25hours",
        help="Destination directory",
    )
    parser.add_argument(
        "--download-dir",
        default=None,
        help="Directory to store source parquet shards locally",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=0,
        help="Stop after this many samples, 0 means all samples",
    )
    parser.add_argument(
        "--cleanup-shards",
        action="store_true",
        help="Delete parquet shards after they are processed",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    wav_dir = output_dir / "wavs"
    wav_dir.mkdir(parents=True, exist_ok=True)
    download_dir = (
        Path(args.download_dir)
        if args.download_dir
        else output_dir / "_downloads" / args.split
    )
    download_dir.mkdir(parents=True, exist_ok=True)

    metadata_rows = []
    sample_count = 0

    for parquet_path in tqdm(iter_local_parquets(args.dataset, args.split, download_dir), desc="Reading parquet shards"):
        table = pq.read_table(parquet_path, columns=["audio", "transcription"])
        for sample in table.to_pylist():
            if args.max_samples and sample_count >= args.max_samples:
                break

            audio = sample["audio"]
            text = str(sample["transcription"]).strip()
            if not text or not audio or not audio.get("bytes"):
                continue

            basename = slugify(Path(audio["path"]).stem or f"infore1_{sample_count:05d}")
            suffix = Path(audio["path"]).suffix or ".wav"
            wav_path = wav_dir / f"{basename}{suffix}"
            wav_path.write_bytes(audio["bytes"])
            metadata_rows.append((basename, text, text))
            sample_count += 1

        del table
        if args.cleanup_shards:
            remove_with_retry(parquet_path)

        if args.max_samples and sample_count >= args.max_samples:
            break

    metadata_path = output_dir / "metadata.csv"
    with metadata_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="|")
        writer.writerows(metadata_rows)

    print(f"Saved {len(metadata_rows)} samples to {output_dir}")
    if args.cleanup_shards:
        print(f"Source parquet shards were cleaned up from {download_dir}")
    else:
        print(f"Source parquet shards stored in {download_dir}")


if __name__ == "__main__":
    main()
