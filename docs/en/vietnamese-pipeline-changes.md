# Vietnamese Pipeline Changes

This document summarizes the main changes added on top of the upstream `ming024/FastSpeech2` repository.

## Main goal

Keep the FastSpeech2 architecture, but adapt the data, text frontend, and workflow for Vietnamese training with `doof-ferb/infore1_25hours`.

## Major changes

### Vietnamese frontend

- added `text/vietnamese.py`
- replaced the old `on_ / v_ / cod_ / tone_` inventory with an IPA-style Vietnamese phone inventory
- kept `phonemize_text()` as a deterministic frontend for Vietnamese transcript processing, but the output is now IPA-style and aligned with the lexicon structure used by the repo

### ViMFA-style organization

- the repo follows the practical organization of `ViMFA`: IPA-style lexicon, `lexicon -> MFA -> TextGrid` workflow, and explicit Vietnamese frontend documentation
- the repo does not bundle the core `ViMFA` resources such as a pretrained G2P model, a pretrained acoustic model, or the exact upstream phone-set package
- the current frontend is deterministic inside this repo, while the G2P model is trained from the exported IPA lexicon data
- because of that, the current repo should be read as a `ViMFA-inspired IPA pipeline`, not a drop-in ViMFA mirror

### Runtime inference order

- Vietnamese synthesis now prefers lexicon lookup for known words
- if a word is missing from the lexicon, the runtime tries the trained MFA G2P model
- if G2P is unavailable or cannot produce a pronunciation, the runtime falls back to the deterministic rule-based frontend

### Dataset download workflow

- rewrote `scripts/download_infore1_dataset.py`
- the dataset is downloaded directly into the project workspace
- parquet shards are cached under `corpus/infore1_25hours/`

### Raw-data preparation for InfoRe1

- added `preprocessor/infore1.py`
- updated `prepare_align.py` to support `InfoRe1`
- the raw preparation stage creates `.wav`, `.lab`, and `.phones`

### Full MFA alignment path

- added `scripts/build_infore1_mfa_assets.py`
- added `scripts/run_mfa_train_alignment.py`
- added `scripts/train_vietnamese_g2p.py`
- added `scripts/prepare_infore1.ps1`
- added `scripts/prepare_infore1_mfa.ps1`
- the full path exports the IPA lexicon, G2P training data, word list, and symbol map before training the G2P model and running MFA acoustic alignment

### Runtime compatibility fixes

- updated audio, preprocessing, and vocoder loading for the current Python/librosa/runtime stack
- improved error handling when the vocoder checkpoint is missing

### HiFi-GAN management

- added `scripts/download_hifigan_pretrained.py`
- updated vocoder loading so missing checkpoints fail with a clearer error message

### Kaggle workflow

- added `requirements-kaggle.txt`
- the clean repo is prepared for GitHub sharing and Kaggle runs
- Kaggle notebooks are kept outside the Git repo in the workspace

### Optional remote services

- added `api/train_infer_api.py`
- added `api/embed_api.py`
- added `scripts/start_ngrok_services.py`

## Important note

The clean repo and the local data-heavy repo are not the same thing.
The clean repo is the shareable version, intended for GitHub and reproducible Kaggle runs.
