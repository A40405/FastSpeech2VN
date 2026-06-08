import csv
import os
import json

import librosa
import numpy as np
from scipy.io import wavfile
from tqdm import tqdm

from text.vietnamese import normalize_text, text_to_phone_tokens


def prepare_align(config):
    in_dir = config["path"]["corpus_path"]
    out_dir = config["path"]["raw_path"]
    sampling_rate = config["preprocessing"]["audio"]["sampling_rate"]
    max_wav_value = config["preprocessing"]["audio"]["max_wav_value"]
    speaker = "InfoRe1"
    report = {
        "samples_seen": 0,
        "samples_written": 0,
        "samples_skipped": 0,
        "skip_reasons": {},
    }

    with open(os.path.join(in_dir, "metadata.csv"), encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="|")
        for parts in tqdm(reader):
            report["samples_seen"] += 1
            if len(parts) < 3:
                report["samples_skipped"] += 1
                report["skip_reasons"]["invalid_metadata_row"] = (
                    report["skip_reasons"].get("invalid_metadata_row", 0) + 1
                )
                continue

            base_name = parts[0]
            raw_text = normalize_text(parts[2])
            if not raw_text:
                report["samples_skipped"] += 1
                report["skip_reasons"]["empty_text"] = (
                    report["skip_reasons"].get("empty_text", 0) + 1
                )
                continue
            phone_tokens = text_to_phone_tokens(raw_text)
            if not phone_tokens or all(token == "spn" for token in phone_tokens):
                report["samples_skipped"] += 1
                report["skip_reasons"]["invalid_phone_tokens"] = (
                    report["skip_reasons"].get("invalid_phone_tokens", 0) + 1
                )
                continue

            wav_path = os.path.join(in_dir, "wavs", f"{base_name}.wav")
            if os.path.exists(wav_path):
                speaker_dir = os.path.join(out_dir, speaker)
                os.makedirs(speaker_dir, exist_ok=True)
                wav, _ = librosa.load(wav_path, sr=sampling_rate)
                wav = np.clip(wav, -1.0, 1.0)
                wavfile.write(
                    os.path.join(speaker_dir, f"{base_name}.wav"),
                    sampling_rate,
                    (wav * max_wav_value).astype(np.int16),
                )
                with open(
                    os.path.join(speaker_dir, f"{base_name}.lab"),
                    "w",
                    encoding="utf-8",
                ) as lab_f:
                    lab_f.write(raw_text)
                with open(
                    os.path.join(speaker_dir, f"{base_name}.phones"),
                    "w",
                    encoding="utf-8",
                ) as phone_f:
                    phone_f.write(" ".join(phone_tokens))
                report["samples_written"] += 1
            else:
                report["samples_skipped"] += 1
                report["skip_reasons"]["missing_wav"] = (
                    report["skip_reasons"].get("missing_wav", 0) + 1
                )

    os.makedirs(out_dir, exist_ok=True)
    with open(
        os.path.join(out_dir, "prepare_align_report.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
