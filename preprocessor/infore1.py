import csv
import os

import librosa
import numpy as np
from scipy.io import wavfile
from tqdm import tqdm

from text.vietnamese import text_to_phone_tokens


def prepare_align(config):
    in_dir = config["path"]["corpus_path"]
    out_dir = config["path"]["raw_path"]
    sampling_rate = config["preprocessing"]["audio"]["sampling_rate"]
    max_wav_value = config["preprocessing"]["audio"]["max_wav_value"]
    speaker = "InfoRe1"

    with open(os.path.join(in_dir, "metadata.csv"), encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="|")
        for parts in tqdm(reader):
            if len(parts) < 3:
                continue

            base_name = parts[0]
            raw_text = parts[2].strip()
            phone_tokens = text_to_phone_tokens(raw_text)

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
