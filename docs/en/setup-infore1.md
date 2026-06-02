# InfoRe1 Setup

This repository keeps the FastSpeech2 architecture and adds a Vietnamese pipeline for the Hugging Face dataset `doof-ferb/infore1_25hours`.

## What this repo is for

- download InfoRe1 into the workspace instead of relying on `.cache/huggingface`
- convert Vietnamese transcripts into the repo's custom phone inventory
- prepare raw files for training
- support two alignment paths:
  - a quick bootstrap TextGrid path for smoke tests
  - a more serious MFA-based alignment path for better duration and boundary quality
- train and infer with FastSpeech2

## Main environments

### Kaggle

Use:

- `kaggle_fastspeech2vn.ipynb`
- `requirements-kaggle.txt`

This is the recommended path if you want GPU training with the clean repo.

### Local machine

Use:

- `requirements-llama_gpu.txt`
- `scripts/prepare_infore1.ps1` for the quick bootstrap path
- `scripts/prepare_infore1_mfa.ps1` for the more serious MFA path

## Quick bootstrap path

Install packages:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' -m pip install -r .\requirements-llama_gpu.txt
```

Prepare data:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1
```

Train:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\train.py -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

## Serious MFA path

If you want better phone boundaries and duration targets, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1_mfa.ps1
```

Detailed guide:

- `mfa-vietnamese-alignment.md`

## Notes

- The clean repo currently has only `config/InfoRe1_25hours/train.yaml`.
- In this clean repo, `train.yaml` is the active training config used by the Kaggle notebook.
- If you run on a weaker local GPU, you may need to reduce `batch_size` or increase `grad_acc_step`.
