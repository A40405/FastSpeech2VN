# InfoRe1 Setup

This repository keeps the FastSpeech2 architecture and adds a Vietnamese pipeline for the Hugging Face dataset `doof-ferb/infore1_25hours`.

## What this repo is for

- download InfoRe1 into the workspace instead of relying on `.cache/huggingface`
- convert Vietnamese transcripts into an IPA-style phone inventory defined in `text/vietnamese.py`
- prepare raw files for training
- export ViMFA-style assets for MFA and G2P:
  - `mfa_assets/infore1_vi.dict`
  - `mfa_assets/infore1_vi_g2p.tsv`
  - `mfa_assets/infore1_vi.wordlist`
  - `mfa_assets/infore1_vi_symbol_map.tsv`
- train a reusable MFA G2P model from the exported IPA lexicon data
- run MFA alignment and FastSpeech2 preprocessing in one full pipeline
- train and infer with FastSpeech2

## Main environments

### Kaggle

Use `requirements-kaggle.txt`.
Keep the Kaggle notebook outside the Git repo in your workspace.

### Local machine

Use:

- `requirements-llama_gpu.txt`
- `scripts/prepare_infore1.ps1` or `scripts/prepare_infore1_mfa.ps1` for the full pipeline

## IPA frontend notes

The repo now uses an IPA-style Vietnamese token inventory instead of the old custom `on_ / v_ / cod_ / tone_` labels.
That means the `.phones` files, MFA lexicon, G2P training data, and FastSpeech2 text symbols all share the same Vietnamese IPA-style labels.

The repo is still not a drop-in copy of `ViMFA`, but it now exposes the same practical building blocks: pronunciation dictionary data, G2P training data, word lists, and symbol mapping.

## Full local pipeline

Install packages:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' -m pip install -r .\requirements-llama_gpu.txt
```

Run the full InfoRe1 pipeline:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1
```

The wrapper script calls the full MFA pipeline, including G2P training.

## Serious MFA path

If you want to run the full pipeline explicitly, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1_mfa.ps1
```

If you also want to train an MFA G2P model from the exported Vietnamese IPA lexicon data, run:

```powershell
python .\scripts\train_vietnamese_g2p.py --mfa mfa --dictionary-path .\mfa_assets\infore1_vi_g2p.tsv --output-model-path .\mfa_assets\infore1_vi_g2p_model.zip --overwrite
```

Detailed guide:

- `mfa-vietnamese-alignment.md`

## Notes

- The clean repo currently has only `config/InfoRe1_25hours/train.yaml`.
- In this clean repo, `train.yaml` is the active training config used by the Kaggle notebook.
- If you run on a weaker local GPU, you may need to reduce `batch_size` or increase `grad_acc_step`.
