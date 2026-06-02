# Vietnamese Pipeline Changes

This document summarizes the project-specific changes made on top of the upstream `ming024/FastSpeech2` repository.

## Main goal

Keep the FastSpeech2 architecture while adapting the data, text frontend, and workflow for Vietnamese training on `doof-ferb/infore1_25hours`.

## Major changes

### Vietnamese text frontend

- added `text/vietnamese.py`
- added a custom Vietnamese phone inventory
- added rule-based `phonemize_text()` for Vietnamese transcript processing

### Dataset download workflow

- rewrote `scripts/download_infore1_dataset.py`
- dataset is downloaded into the project workspace instead of depending on `.cache/huggingface`
- extracted files go to `corpus/infore1_25hours/`

### InfoRe1 raw-data preparation

- added `preprocessor/infore1.py`
- updated `prepare_align.py` to support `InfoRe1`
- raw preparation now writes `.wav`, `.lab`, and `.phones`

### Bootstrap alignment path

- updated `scripts/bootstrap_textgrids.py`
- bootstrap TextGrids are generated from `.phones`
- this is intended for smoke tests and quick setup only

### Serious MFA alignment path

- added `scripts/build_infore1_mfa_assets.py`
- added `scripts/run_mfa_train_alignment.py`
- added `scripts/prepare_infore1_mfa.ps1`
- this path trains MFA on the repo's own phone inventory and exports real TextGrids

### Runtime compatibility fixes

- updated audio, preprocessing, and vocoder-loading paths for the current Python/librosa/runtime stack
- improved failure handling when vocoder checkpoints are missing

### HiFi-GAN handling

- added `scripts/download_hifigan_pretrained.py`
- updated vocoder loading so missing checkpoints are handled more clearly

### Kaggle workflow

- added `kaggle_fastspeech2vn.ipynb`
- added `requirements-kaggle.txt`
- the clean repo is prepared for Kaggle notebook usage and reproducible sharing

### Optional remote service layer

- added `api/train_infer_api.py`
- added `api/embed_api.py`
- added `scripts/start_ngrok_services.py`

## Important note

The clean repo and the local working repo are not the same thing.
This clean repo is the shareable, lighter version intended for GitHub and Kaggle.
