import os
import random
import json

import tgt
import librosa
import numpy as np
import pyworld as pw
from scipy.interpolate import interp1d
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

import audio as Audio
from preprocessor.alignment_utils import (
    build_alignment_settings,
    make_interval,
    sanitize_alignment_intervals,
)
from utils.io import atomic_write_json


class Preprocessor:
    def __init__(self, config):
        self.config = config
        self.in_dir = config["path"]["raw_path"]
        self.out_dir = config["path"]["preprocessed_path"]
        self.val_size = config["preprocessing"]["val_size"]
        self.sampling_rate = config["preprocessing"]["audio"]["sampling_rate"]
        self.hop_length = config["preprocessing"]["stft"]["hop_length"]
        self.alignment_settings = build_alignment_settings(config)

        assert config["preprocessing"]["pitch"]["feature"] in [
            "phoneme_level",
            "frame_level",
        ]
        assert config["preprocessing"]["energy"]["feature"] in [
            "phoneme_level",
            "frame_level",
        ]
        self.pitch_phoneme_averaging = (
            config["preprocessing"]["pitch"]["feature"] == "phoneme_level"
        )
        self.energy_phoneme_averaging = (
            config["preprocessing"]["energy"]["feature"] == "phoneme_level"
        )

        self.pitch_normalization = config["preprocessing"]["pitch"]["normalization"]
        self.energy_normalization = config["preprocessing"]["energy"]["normalization"]

        self.STFT = Audio.stft.TacotronSTFT(
            config["preprocessing"]["stft"]["filter_length"],
            config["preprocessing"]["stft"]["hop_length"],
            config["preprocessing"]["stft"]["win_length"],
            config["preprocessing"]["mel"]["n_mel_channels"],
            config["preprocessing"]["audio"]["sampling_rate"],
            config["preprocessing"]["mel"]["mel_fmin"],
            config["preprocessing"]["mel"]["mel_fmax"],
        )

    def build_from_path(self):
        os.makedirs((os.path.join(self.out_dir, "mel")), exist_ok=True)
        os.makedirs((os.path.join(self.out_dir, "pitch")), exist_ok=True)
        os.makedirs((os.path.join(self.out_dir, "energy")), exist_ok=True)
        os.makedirs((os.path.join(self.out_dir, "duration")), exist_ok=True)

        print("Processing Data ...")
        out = list()
        n_frames = 0
        pitch_scaler = StandardScaler()
        energy_scaler = StandardScaler()
        alignment_report = {
            "summary": {
                "samples_seen": 0,
                "samples_processed": 0,
                "samples_dropped": 0,
            },
            "detected_counts": {},
            "repaired_counts": {},
            "dropped_counts": {},
            "drop_reasons": {},
            "examples": {
                "dropped_samples": [],
                "detected_issues": [],
            },
        }

        # Compute pitch, energy, duration, and mel-spectrogram
        speakers = {}
        for i, speaker in enumerate(tqdm(os.listdir(self.in_dir))):
            speakers[speaker] = i
            for wav_name in os.listdir(os.path.join(self.in_dir, speaker)):
                if ".wav" not in wav_name:
                    continue

                basename = wav_name.split(".")[0]
                tg_path = os.path.join(
                    self.out_dir, "TextGrid", speaker, "{}.TextGrid".format(basename)
                )
                if os.path.exists(tg_path):
                    alignment_report["summary"]["samples_seen"] += 1
                    result = self.process_utterance(speaker, basename)
                    self.update_alignment_report(
                        alignment_report, speaker, basename, result["report"]
                    )
                    if result["status"] != "ok":
                        continue
                    info = result["info"]
                    pitch = result["pitch"]
                    energy = result["energy"]
                    n = result["n_frames"]
                    out.append(info)
                    alignment_report["summary"]["samples_processed"] += 1
                else:
                    alignment_report["summary"]["samples_seen"] += 1
                    self.update_alignment_report(
                        alignment_report,
                        speaker,
                        basename,
                        {"drop_reason": "missing_textgrid"},
                    )
                    continue

                if len(pitch) > 0:
                    pitch_scaler.partial_fit(pitch.reshape((-1, 1)))
                if len(energy) > 0:
                    energy_scaler.partial_fit(energy.reshape((-1, 1)))

                n_frames += n

        print("Computing statistic quantities ...")
        # Perform normalization if necessary
        if self.pitch_normalization:
            pitch_mean = pitch_scaler.mean_[0]
            pitch_std = pitch_scaler.scale_[0]
        else:
            # A numerical trick to avoid normalization...
            pitch_mean = 0
            pitch_std = 1
        if self.energy_normalization:
            energy_mean = energy_scaler.mean_[0]
            energy_std = energy_scaler.scale_[0]
        else:
            energy_mean = 0
            energy_std = 1

        pitch_min, pitch_max = self.normalize(
            os.path.join(self.out_dir, "pitch"), pitch_mean, pitch_std
        )
        energy_min, energy_max = self.normalize(
            os.path.join(self.out_dir, "energy"), energy_mean, energy_std
        )

        # Save files
        with open(os.path.join(self.out_dir, "speakers.json"), "w") as f:
            f.write(json.dumps(speakers))

        with open(os.path.join(self.out_dir, "stats.json"), "w") as f:
            stats = {
                "pitch": [
                    float(pitch_min),
                    float(pitch_max),
                    float(pitch_mean),
                    float(pitch_std),
                ],
                "energy": [
                    float(energy_min),
                    float(energy_max),
                    float(energy_mean),
                    float(energy_std),
                ],
            }
            f.write(json.dumps(stats))
        atomic_write_json(
            alignment_report,
            os.path.join(self.out_dir, "alignment_report.json"),
        )

        print(
            "Total time: {} hours".format(
                n_frames * self.hop_length / self.sampling_rate / 3600
            )
        )

        random.shuffle(out)
        out = [r for r in out if r is not None]

        # Write metadata
        with open(os.path.join(self.out_dir, "train.txt"), "w", encoding="utf-8") as f:
            for m in out[self.val_size :]:
                f.write(m + "\n")
        with open(os.path.join(self.out_dir, "val.txt"), "w", encoding="utf-8") as f:
            for m in out[: self.val_size]:
                f.write(m + "\n")

        return out

    def process_utterance(self, speaker, basename):
        wav_path = os.path.join(self.in_dir, speaker, "{}.wav".format(basename))
        text_path = os.path.join(self.in_dir, speaker, "{}.lab".format(basename))
        tg_path = os.path.join(
            self.out_dir, "TextGrid", speaker, "{}.TextGrid".format(basename)
        )

        # Get alignments
        try:
            textgrid = tgt.io.read_textgrid(tg_path)
            phone, duration, start, end, alignment_info = self.get_alignment(
                textgrid.get_tier_by_name("phones")
            )
        except Exception as exc:
            return {
                "status": "dropped",
                "report": {
                    "drop_reason": "alignment_parse_error",
                    "error_message": str(exc),
                },
            }

        text = "{" + " ".join(phone) + "}"
        if start >= end:
            return {
                "status": "dropped",
                "report": {
                    **alignment_info,
                    "drop_reason": "invalid_trimmed_range",
                },
            }

        # Read and trim wav files
        wav, _ = librosa.load(wav_path, sr=self.sampling_rate)
        wav = wav[
            int(self.sampling_rate * start) : int(self.sampling_rate * end)
        ].astype(np.float32)

        # Read raw text
        with open(text_path, "r", encoding="utf-8") as f:
            raw_text = f.readline().strip("\n")

        # Compute fundamental frequency
        pitch, t = pw.dio(
            wav.astype(np.float64),
            self.sampling_rate,
            frame_period=self.hop_length / self.sampling_rate * 1000,
        )
        pitch = pw.stonemask(wav.astype(np.float64), pitch, t, self.sampling_rate)

        pitch = pitch[: sum(duration)]
        if np.sum(pitch != 0) <= 1:
            return {
                "status": "dropped",
                "report": {
                    **alignment_info,
                    "drop_reason": "insufficient_voiced_pitch",
                },
            }

        # Compute mel-scale spectrogram and energy
        mel_spectrogram, energy = Audio.tools.get_mel_from_wav(wav, self.STFT)
        mel_spectrogram = mel_spectrogram[:, : sum(duration)].astype(np.float32)
        energy = energy[: sum(duration)].astype(np.float32)

        if self.pitch_phoneme_averaging:
            # perform linear interpolation
            nonzero_ids = np.where(pitch != 0)[0]
            interp_fn = interp1d(
                nonzero_ids,
                pitch[nonzero_ids],
                fill_value=(pitch[nonzero_ids[0]], pitch[nonzero_ids[-1]]),
                bounds_error=False,
            )
            pitch = interp_fn(np.arange(0, len(pitch)))

            # Phoneme-level average
            pos = 0
            for i, d in enumerate(duration):
                if d > 0:
                    pitch[i] = np.mean(pitch[pos : pos + d])
                else:
                    pitch[i] = 0
                pos += d
            pitch = pitch[: len(duration)].astype(np.float32)

        if self.energy_phoneme_averaging:
            # Phoneme-level average
            pos = 0
            for i, d in enumerate(duration):
                if d > 0:
                    energy[i] = np.mean(energy[pos : pos + d])
                else:
                    energy[i] = 0
                pos += d
            energy = energy[: len(duration)].astype(np.float32)

        pitch = pitch.astype(np.float32)
        energy = energy.astype(np.float32)
        duration = np.asarray(duration, dtype=np.int64)

        # Save files
        dur_filename = "{}-duration-{}.npy".format(speaker, basename)
        np.save(os.path.join(self.out_dir, "duration", dur_filename), duration)

        pitch_filename = "{}-pitch-{}.npy".format(speaker, basename)
        np.save(os.path.join(self.out_dir, "pitch", pitch_filename), pitch)

        energy_filename = "{}-energy-{}.npy".format(speaker, basename)
        np.save(os.path.join(self.out_dir, "energy", energy_filename), energy)

        mel_filename = "{}-mel-{}.npy".format(speaker, basename)
        np.save(
            os.path.join(self.out_dir, "mel", mel_filename),
            mel_spectrogram.T.astype(np.float32),
        )

        return {
            "status": "ok",
            "info": "|".join([basename, speaker, text, raw_text]),
            "pitch": self.remove_outlier(pitch),
            "energy": self.remove_outlier(energy),
            "n_frames": mel_spectrogram.shape[1],
            "report": alignment_info,
        }

    def get_alignment(self, tier):
        intervals = []
        for interval in tier._objects:
            start = float(interval.start_time)
            end = float(interval.end_time)
            duration = int(
                np.round(end * self.sampling_rate / self.hop_length)
                - np.round(start * self.sampling_rate / self.hop_length)
            )
            intervals.append(
                make_interval(start, end, interval.text, duration)
            )

        alignment_result = sanitize_alignment_intervals(intervals, self.alignment_settings)
        sanitized_intervals = alignment_result["intervals"]
        if not alignment_result["valid"]:
            return [], [], 0, 0, alignment_result

        phones = [entry["phone"] for entry in sanitized_intervals]
        durations = [entry["duration"] for entry in sanitized_intervals]
        start_time = sanitized_intervals[0]["start"]
        end_time = sanitized_intervals[-1]["end"]

        return phones, durations, start_time, end_time, alignment_result

    def update_alignment_report(self, report, speaker, basename, sample_report):
        drop_reason = sample_report.get("drop_reason")
        if drop_reason:
            report["summary"]["samples_dropped"] += 1
            report["drop_reasons"][drop_reason] = (
                report["drop_reasons"].get(drop_reason, 0) + 1
            )
            dropped_examples = report["examples"]["dropped_samples"]
            if len(dropped_examples) < 20:
                dropped_examples.append(
                    {
                        "speaker": speaker,
                        "basename": basename,
                        "reason": drop_reason,
                        "fatal_errors": sample_report.get("fatal_errors", []),
                        "error_message": sample_report.get("error_message"),
                    }
                )

        for group_name in ("detected_counts", "repaired_counts", "dropped_counts"):
            group_counts = sample_report.get(group_name, {})
            for key, value in group_counts.items():
                report[group_name][key] = report[group_name].get(key, 0) + int(value)

        if sample_report.get("examples") and len(report["examples"]["detected_issues"]) < 20:
            report["examples"]["detected_issues"].append(
                {
                    "speaker": speaker,
                    "basename": basename,
                    "examples": sample_report["examples"],
                }
            )

    def remove_outlier(self, values):
        values = np.array(values)
        p25 = np.percentile(values, 25)
        p75 = np.percentile(values, 75)
        lower = p25 - 1.5 * (p75 - p25)
        upper = p75 + 1.5 * (p75 - p25)
        normal_indices = np.logical_and(values > lower, values < upper)

        return values[normal_indices]

    def normalize(self, in_dir, mean, std):
        max_value = np.finfo(np.float64).min
        min_value = np.finfo(np.float64).max
        for filename in os.listdir(in_dir):
            filename = os.path.join(in_dir, filename)
            values = ((np.load(filename).astype(np.float32) - mean) / std).astype(
                np.float32
            )
            np.save(filename, values)

            max_value = max(max_value, max(values))
            min_value = min(min_value, min(values))

        return min_value, max_value
