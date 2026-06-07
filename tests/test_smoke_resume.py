import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import yaml
from scipy.io import wavfile


def deps_available():
    try:
        import tgt  # noqa: F401
        import pyworld  # noqa: F401
        import librosa  # noqa: F401
        return True
    except Exception:
        return False


@unittest.skipUnless(deps_available(), "smoke test requires tgt/librosa/pyworld")
class SmokeResumeTest(unittest.TestCase):
    def test_preprocess_train_and_resume(self):
        import tgt

        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            raw_root = root / "raw_data" / "InfoRe1" / "InfoRe1"
            textgrid_root = root / "preprocessed_data" / "InfoRe1" / "TextGrid" / "InfoRe1"
            raw_root.mkdir(parents=True, exist_ok=True)
            textgrid_root.mkdir(parents=True, exist_ok=True)

            sr = 22050
            duration_sec = 0.9
            t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
            wav = (0.2 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)

            samples = {
                "0001": ("ma", [("m", 0.0, 0.2), ("a", 0.2, 0.45), ("˧", 0.45, 0.9)]),
                "0002": ("mi", [("m", 0.0, 0.18), ("i", 0.18, 0.44), ("˧", 0.44, 0.9)]),
                "0003": ("mu", [("m", 0.0, 0.22), ("u", 0.22, 0.5), ("˧", 0.5, 0.9)]),
            }

            for basename, (raw_text, phones) in samples.items():
                wavfile.write(raw_root / f"{basename}.wav", sr, (wav * 32767).astype(np.int16))
                (raw_root / f"{basename}.lab").write_text(raw_text, encoding="utf-8")

                textgrid = tgt.TextGrid()
                phone_tier = tgt.IntervalTier(name="phones")
                for phone, start, end in phones:
                    phone_tier.add_interval(tgt.Interval(start, end, phone))
                textgrid.add_tier(phone_tier)
                tgt.io.write_to_file(
                    textgrid,
                    str(textgrid_root / f"{basename}.TextGrid"),
                    format="long",
                )

            preprocess_config = {
                "dataset": "InfoRe1",
                "path": {
                    "raw_path": str(root / "raw_data" / "InfoRe1"),
                    "preprocessed_path": str(root / "preprocessed_data" / "InfoRe1"),
                    "lexicon_path": str(root / "mfa_assets" / "infore1_vi.dict"),
                    "g2p_model_path": str(root / "mfa_assets" / "infore1_vi_g2p_model.zip"),
                },
                "preprocessing": {
                    "val_size": 1,
                    "text": {"text_cleaners": ["basic_cleaners"], "language": "vi"},
                    "alignment": {
                        "silence_labels": ["", "sil", "sp", "spn"],
                        "pause_phone": "sp",
                        "repair_zero_durations": True,
                        "drop_unrecoverable_zero_durations": True,
                        "collapse_consecutive_pauses": True,
                    },
                    "audio": {"sampling_rate": sr, "max_wav_value": 32768.0},
                    "stft": {"filter_length": 1024, "hop_length": 256, "win_length": 1024},
                    "mel": {
                        "n_mel_channels": 80,
                        "mel_fmin": 0,
                        "mel_fmax": 8000,
                    },
                    "pitch": {"feature": "frame_level", "normalization": True},
                    "energy": {"feature": "phoneme_level", "normalization": True},
                },
            }
            model_config = {
                "transformer": {
                    "encoder_layer": 1,
                    "encoder_head": 2,
                    "encoder_hidden": 16,
                    "decoder_layer": 1,
                    "decoder_head": 2,
                    "decoder_hidden": 16,
                    "conv_filter_size": 32,
                    "conv_kernel_size": [9, 1],
                    "encoder_dropout": 0.1,
                    "decoder_dropout": 0.1,
                },
                "variance_predictor": {
                    "filter_size": 16,
                    "kernel_size": 3,
                    "dropout": 0.1,
                },
                "variance_embedding": {
                    "pitch_quantization": "linear",
                    "energy_quantization": "linear",
                    "n_bins": 32,
                },
                "multi_speaker": False,
                "max_seq_len": 100,
                "vocoder": {"model": "", "speaker": "universal"},
            }
            train_config = {
                "path": {
                    "ckpt_path": str(root / "output" / "ckpt" / "InfoRe1"),
                    "log_path": str(root / "output" / "log" / "InfoRe1"),
                    "result_path": str(root / "output" / "result" / "InfoRe1"),
                },
                "optimizer": {
                    "batch_size": 1,
                    "betas": [0.9, 0.98],
                    "eps": 1e-9,
                    "weight_decay": 0.0,
                    "grad_clip_thresh": 1.0,
                    "grad_acc_step": 1,
                    "warm_up_step": 10,
                    "anneal_steps": [],
                    "anneal_rate": 0.3,
                },
                "step": {
                    "total_step": 1,
                    "log_step": 1,
                    "synth_step": 999,
                    "val_step": 1,
                    "save_step": 1,
                    "keep_best_ckpts": 3,
                },
                "dataloader": {
                    "group_size": 1,
                    "num_workers": 0,
                    "pin_memory": False,
                    "persistent_workers": False,
                    "prefetch_factor": 2,
                },
                "accelerator": {"use_amp": False, "cudnn_benchmark": False},
            }

            preprocess_path = root / "preprocess.yaml"
            model_path = root / "model.yaml"
            train_path = root / "train.yaml"
            preprocess_path.write_text(yaml.safe_dump(preprocess_config, sort_keys=False), encoding="utf-8")
            model_path.write_text(yaml.safe_dump(model_config, sort_keys=False), encoding="utf-8")
            train_path.write_text(yaml.safe_dump(train_config, sort_keys=False), encoding="utf-8")

            subprocess.run(
                [sys.executable, "preprocess.py", str(preprocess_path)],
                cwd=repo_root,
                check=True,
            )

            subprocess.run(
                [
                    sys.executable,
                    "train.py",
                    "-p",
                    str(preprocess_path),
                    "-m",
                    str(model_path),
                    "-t",
                    str(train_path),
                ],
                cwd=repo_root,
                check=True,
            )

            latest_metadata_path = Path(train_config["path"]["ckpt_path"]) / "latest_checkpoint.json"
            latest_1 = json.loads(latest_metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(latest_1["step"], 1)

            train_config["step"]["total_step"] = 2
            train_path.write_text(yaml.safe_dump(train_config, sort_keys=False), encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    "train.py",
                    "--restore_step",
                    str(latest_1["step"]),
                    "-p",
                    str(preprocess_path),
                    "-m",
                    str(model_path),
                    "-t",
                    str(train_path),
                ],
                cwd=repo_root,
                check=True,
            )

            latest_2 = json.loads(latest_metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(latest_2["step"], 2)
            self.assertGreaterEqual(latest_2["epoch"], latest_1["epoch"])


if __name__ == "__main__":
    unittest.main()
