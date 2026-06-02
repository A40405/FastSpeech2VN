# Local Train Guide

This guide is the end-to-end local workflow for the clean repo.

## 1) Install packages

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' -m pip install -r .\requirements-llama_gpu.txt
```

## 2) Download the dataset

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\download_infore1_dataset.py --dataset doof-ferb/infore1_25hours --split train --output-dir .\corpus\infore1_25hours
```

Expected outputs:

- `corpus/infore1_25hours/metadata.csv`
- `corpus/infore1_25hours/wavs/*.wav`
- `corpus/infore1_25hours/_downloads/train/*.parquet`

## 3) Prepare raw files

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\prepare_align.py .\config\InfoRe1_25hours\preprocess.yaml
```

Expected outputs:

- `raw_data/InfoRe1/InfoRe1/*.wav`
- `raw_data/InfoRe1/InfoRe1/*.lab`
- `raw_data/InfoRe1/InfoRe1/*.phones`

## 4) Choose an alignment path

### Option A: quick bootstrap path

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\bootstrap_textgrids.py --raw-root .\raw_data\InfoRe1 --output-root .\preprocessed_data\InfoRe1\TextGrid
```

### Option B: serious MFA path

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1_mfa.ps1
```

If you use the MFA path, it will already run download, prepare-align, MFA asset generation, MFA training/alignment export, and `preprocess.py`.

Detailed guide:

- `mfa-vietnamese-alignment.md`

## 5) Preprocess acoustic features

Run this step only if you used the bootstrap path:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\preprocess.py .\config\InfoRe1_25hours\preprocess.yaml
```

## 6) Train FastSpeech2

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\train.py -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

## 7) TensorBoard

```powershell
& 'C:\Users\anhhu\AppData\Roaming\Python\Python310\Scripts\tensorboard.exe' --logdir .\output\log\InfoRe1
```

## 8) High-quality WAV inference

Download HiFi-GAN pretrained weights:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\download_hifigan_pretrained.py
```

Infer:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\synthesize.py --mode single --text "xin chao, day la fastspeech hai tieng viet" --restore_step 9000 -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

## 9) Important note about this clean repo

The clean repo is mainly prepared for Kaggle and reproducible sharing.
If your local GPU is weaker than Kaggle T4, you may need to reduce `batch_size` in `config/InfoRe1_25hours/train.yaml`.

## 10) Common issues

- `UnicodeDecodeError`: make sure text files are UTF-8.
- `TypeError: mel() takes 0 positional arguments`: this repo already includes the librosa compatibility fix.
- missing vocoder checkpoint: run `python .\scripts\download_hifigan_pretrained.py`.
- MFA not found: install Montreal Forced Aligner first and check `mfa version`.
