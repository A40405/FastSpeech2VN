# FastSpeech2 InfoRe1 Setup

This workspace uses the FastSpeech2 architecture from `ming024/FastSpeech2`, adapted for the Hugging Face dataset `doof-ferb/infore1_25hours`.

## What is customized

- Source code is downloaded without `git clone`.
- The dataset is downloaded from Hugging Face as parquet shards directly into the workspace.
- Transcript text is converted into Vietnamese phoneme tokens with `text/vietnamese.py`.
- `prepare_align.py` now writes both `.lab` (raw text) and `.phones` (phoneme tokens).
- `scripts/bootstrap_textgrids.py` builds phone-level TextGrid using `.phones`.
- The training config is tuned for a 4 GB GPU and does not require a vocoder checkpoint to start training.

## Environment

This setup now uses the existing conda environment:

```powershell
D:\Anaconda\envs\llama_gpu\python.exe
```

The extra packages needed on top of `llama_gpu` are collected in:

```powershell
.\requirements-llama_gpu.txt
```

Install them with:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' -m pip install -r .\requirements-llama_gpu.txt
```

## Dataset + preprocessing

Run the full preparation pipeline:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1
```

If you prefer step by step:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\download_infore1_dataset.py --dataset doof-ferb/infore1_25hours --output-dir .\corpus\infore1_25hours
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\prepare_align.py .\config\InfoRe1_25hours\preprocess.yaml
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\bootstrap_textgrids.py --raw-root .\raw_data\InfoRe1 --output-root .\preprocessed_data\InfoRe1\TextGrid
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\preprocess.py .\config\InfoRe1_25hours\preprocess.yaml
```

## Train

Start training with:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\train.py -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

TensorBoard:

```powershell
& 'C:\Users\anhhu\AppData\Roaming\Python\Python310\Scripts\tensorboard.exe' --logdir .\output\log\InfoRe1
```

## Notes

- The default bootstrap TextGrid path is the fastest way to get a trainable FastSpeech2 pipeline on this machine.
- Hugging Face parquet sources are stored inside `corpus/infore1_25hours/_downloads`, not in `.cache/huggingface`.
- The Vietnamese frontend here is a rule-based phoneme pipeline (onset, nucleus, coda, tone tokens).
