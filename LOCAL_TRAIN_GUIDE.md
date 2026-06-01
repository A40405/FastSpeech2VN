# Local Train Guide (InfoRe1 Vietnamese FastSpeech2)

This guide is a full local runbook from data download to training and inference.

## 1) Environment

Use existing conda env:

```powershell
D:\Anaconda\envs\llama_gpu\python.exe
```

Install dependencies:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' -m pip install -r .\requirements-llama_gpu.txt
```

## 2) Download dataset

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\download_infore1_dataset.py --dataset doof-ferb/infore1_25hours --split train --output-dir .\corpus\infore1_25hours
```

Expected output artifacts:

- `corpus/infore1_25hours/metadata.csv`
- `corpus/infore1_25hours/wavs/*.wav`
- `corpus/infore1_25hours/_downloads/train/*.parquet`

## 3) Prepare align input

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\prepare_align.py .\config\InfoRe1_25hours\preprocess.yaml
```

Expected artifacts:

- `raw_data/InfoRe1/InfoRe1/*.wav`
- `raw_data/InfoRe1/InfoRe1/*.lab`
- `raw_data/InfoRe1/InfoRe1/*.phones`

## 4) Bootstrap TextGrid

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\bootstrap_textgrids.py --raw-root .\raw_data\InfoRe1 --output-root .\preprocessed_data\InfoRe1\TextGrid
```

Expected artifact:

- `preprocessed_data/InfoRe1/TextGrid/InfoRe1/*.TextGrid`

## 5) Preprocess acoustic features

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\preprocess.py .\config\InfoRe1_25hours\preprocess.yaml
```

Expected artifact groups:

- `preprocessed_data/InfoRe1/mel/*.npy`
- `preprocessed_data/InfoRe1/pitch/*.npy`
- `preprocessed_data/InfoRe1/energy/*.npy`
- `preprocessed_data/InfoRe1/duration/*.npy`
- `preprocessed_data/InfoRe1/train.txt`, `val.txt`, `speakers.json`, `stats.json`

## 6) Train

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\train.py -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

Checkpoint path:

- `output/ckpt/InfoRe1/*.pth.tar` (or the `ckpt_path` defined in `train.yaml`)

TensorBoard:

```powershell
& 'C:\Users\anhhu\AppData\Roaming\Python\Python310\Scripts\tensorboard.exe' --logdir .\output\log\InfoRe1
```

## 7) Inference WAV (high quality)

Download HiFi-GAN pretrained weights:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\download_hifigan_pretrained.py
```

Infer:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\synthesize.py --mode single --text "xin chao, day la fastspeech hai tieng viet" --restore_step 9000 -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

Output WAV:

- `output/result/*.wav`

## 8) One-command preparation option

You can run data prep steps (2-5) with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1
```

## 9) Common issues

- `UnicodeDecodeError` in preprocess: ensure `.lab` is UTF-8 and use current patched code.
- `TypeError: mel() takes 0 positional arguments...`: old librosa call mismatch, fixed in current repo.
- missing vocoder checkpoint: run `python .\scripts\download_hifigan_pretrained.py`.
