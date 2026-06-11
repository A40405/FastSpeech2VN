# Local Train Guide

This guide is the end-to-end local workflow for the clean repo.

## 1) Install packages

```powershell
$env:PYTHON_EXE = "python"
& $env:PYTHON_EXE -m pip install -r .\requirements-llama_gpu.txt
```

## 2) Run the full InfoRe1 pipeline

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1 -PythonExe $env:PYTHON_EXE -MfaExe "mfa"
```

This wrapper script already runs:

- dataset download
- raw file preparation
- MFA asset generation
- G2P model training
- MFA alignment
- alignment and phoneset validation
- FastSpeech2 preprocessing
- clean split generation for `train.clean.txt` and `val.clean.txt`

Detailed guide:

- `mfa-vietnamese-alignment.md`

## 3) Train FastSpeech2

```powershell
& $env:PYTHON_EXE .\train.py -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

`config/InfoRe1_25hours/train.yaml` is now tuned for a safer retrain baseline:

- `batch_size: 4`
- `grad_acc_step: 4`
- `group_size: 2`
- `num_workers: 2`
- AMP disabled by default for easier diagnosis

## 3.1) Build a cleaner subset before retraining

Once `alignment_validation_report.json` exists, generate stricter train/val splits:

```powershell
& $env:PYTHON_EXE .\scripts\build_infore1_clean_subset.py --config .\config\InfoRe1_25hours\preprocess.yaml
```

This writes:

- `preprocessed_data/InfoRe1/train.clean.txt`
- `preprocessed_data/InfoRe1/val.clean.txt`
- `preprocessed_data/InfoRe1/clean_subset_report.json`

The current clean subset preset is intentionally stricter for Vietnamese long-form TTS:

- `min_total_duration_frames: 48`
- `max_zero_duration_repaired: 0`
- `max_one_frame_non_silence_count: 10`
- `max_one_frame_non_silence_ratio: 0.10`
- `max_pause_frame_ratio: 0.25`
- `max_token_count: 110`

This drops many long or noisy samples that often sound fine at the start but degrade near the end.

To train on the clean subset, switch `config/InfoRe1_25hours/train.yaml` to:

```yaml
dataset:
  train_file: "train.clean.txt"
  val_file: "val.clean.txt"
```

## 4) TensorBoard

```powershell
& $env:PYTHON_EXE -m tensorboard.main --logdir .\output\log\InfoRe1
```

## 5) High-quality WAV inference

Download HiFi-GAN pretrained weights:

```powershell
& $env:PYTHON_EXE .\scripts\download_hifigan_pretrained.py
```

Infer:

```powershell
& $env:PYTHON_EXE .\synthesize.py --mode single --text "xin chao, day la fastspeech hai tieng viet" --restore_step 9000 -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

## 6) Important note about this clean repo

The clean repo is mainly prepared for Kaggle and reproducible sharing.
If your local GPU is weaker than Kaggle T4, you may still reduce `batch_size`, but the current preset already favors stability over speed.
After preprocessing, it is worth checking:

- `preprocessed_data/InfoRe1/alignment_validation_report.json`
- `preprocessed_data/InfoRe1/clean_subset_report.json`
- `mfa_assets/phoneset_report.json`

## 6.1) Early checkpoint listening at 8000 / 16000 / 24000

To synthesize the short checkpoint review set:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\evaluate_infore1_checkpoints.ps1 -PythonExe $env:PYTHON_EXE
```

The script renders:

- `xin chào bạn`
- `mời bạn ngồi xuống`
- `hôm nay trời đẹp`

and stores the outputs under `output/result/InfoRe1_eval/step_8000`, `step_16000`, and `step_24000`.

## 7) Common issues

- `UnicodeDecodeError`: make sure text files are UTF-8.
- `TypeError: mel() takes 0 positional arguments`: this repo already includes the librosa compatibility fix.
- missing vocoder checkpoint: run `python .\scripts\download_hifigan_pretrained.py`.
- MFA not found: install Montreal Forced Aligner first and check `mfa version`.
