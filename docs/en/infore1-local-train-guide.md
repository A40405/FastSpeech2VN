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
- FastSpeech2 preprocessing

Detailed guide:

- `mfa-vietnamese-alignment.md`

## 3) Train FastSpeech2

```powershell
& $env:PYTHON_EXE .\train.py -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
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
If your local GPU is weaker than Kaggle T4, you may need to reduce `batch_size` in `config/InfoRe1_25hours/train.yaml`.

## 7) Common issues

- `UnicodeDecodeError`: make sure text files are UTF-8.
- `TypeError: mel() takes 0 positional arguments`: this repo already includes the librosa compatibility fix.
- missing vocoder checkpoint: run `python .\scripts\download_hifigan_pretrained.py`.
- MFA not found: install Montreal Forced Aligner first and check `mfa version`.
