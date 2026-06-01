# Vietnamese Pipeline Changes

This file summarizes all project-level code changes made on top of the cloned `ming024/FastSpeech2` repository to support the Vietnamese training pipeline for dataset `doof-ferb/infore1_25hours`.

## Goal

Keep FastSpeech2 architecture unchanged while adapting data pipeline and text frontend for Vietnamese phoneme-based training.

## Removed Legacy Pieces

- `scripts/build_ascii_lexicon.py`
- `scripts/run_infore1_alignment.ps1`
- `requirements-py310.txt`

These files belonged to an older ASCII-lexicon/MFA branch and are no longer used in the current Vietnamese pipeline.

## New Vietnamese Frontend

### Added

- `text/vietnamese.py`

### What it does

- Normalizes Vietnamese text.
- Converts text into Vietnamese phoneme token sequence (onset, vowel, coda, tone).
- Exposes:
  - `VIETNAMESE_PHONE_TOKENS`
  - `phonemize_text(text)`

## Symbol Inventory Update

### Updated

- `text/symbols.py`

### What changed

- Added Vietnamese phoneme token symbols from `text/vietnamese.py`.
- These tokens are included as `@token` style symbols so `text_to_sequence()` can map them to IDs.

## Dataset Download Pipeline (No HF Cache Dependency)

### Added/Rewritten

- `scripts/download_infore1_dataset.py`

### What changed

- Downloads Hugging Face parquet shards directly to project workspace:
  - `corpus/infore1_25hours/_downloads/<split>/`
- Extracts audio bytes and transcripts from parquet.
- Writes:
  - wav files to `corpus/infore1_25hours/wavs/`
  - metadata to `corpus/infore1_25hours/metadata.csv`

This avoids relying on `.cache/huggingface` as primary dataset storage.

## InfoRe1 Prepare Align Path

### Added

- `preprocessor/infore1.py`

### What it does

- Reads `metadata.csv`.
- Generates:
  - normalized wav in `raw_data/InfoRe1/InfoRe1/*.wav`
  - raw text `.lab`
  - phoneme tokens `.phones` (from Vietnamese frontend)

### Updated

- `prepare_align.py`

### What changed

- Added `InfoRe1` dataset branch:
  - if dataset contains `InfoRe1`, run `preprocessor.infore1.prepare_align()`

## Bootstrap Alignment for Preprocess

### Updated

- `scripts/bootstrap_textgrids.py`

### What changed

- Uses `.phones` token file (not character-level text) to build phone tier `TextGrid`.
- Keeps preprocess path runnable without external MFA setup.

## Config Updates for Vietnamese Dataset

### Updated

- `config/InfoRe1_25hours/preprocess.yaml`

### What changed

- `dataset: "InfoRe1"`
- Removed lexicon path dependency.
- Set Vietnamese text preprocessing mode:
  - `language: "vi"`
  - `text_cleaners: ["basic_cleaners"]`

## End-to-End Prepare Script

### Updated

- `scripts/prepare_infore1.ps1`

### Current pipeline

1. Download dataset to local workspace (`_downloads` + `wavs` + `metadata.csv`)
2. `prepare_align.py` for InfoRe1
3. Bootstrap phone-level TextGrid from `.phones`
4. Run `preprocess.py`

## Vietnamese Inference Path

### Updated

- `synthesize.py`

### What changed

- Added Vietnamese single-sentence preprocessing branch (`language == "vi"`).
- Uses `phonemize_text()` before `text_to_sequence()`.

## Runtime Compatibility Fixes

### Updated

- `audio/stft.py`
- `preprocessor/preprocessor.py`
- `utils/model.py`
- `utils/tools.py`

### Purpose

- Improve runtime compatibility in current environment (PyTorch/librosa/runtime behavior) and avoid hard failures when vocoder checkpoints are unavailable.

## Dependency File Used

### Active dependency file

- `requirements-llama_gpu.txt`

This is the primary requirements file for the current environment workflow.

## HiFi-GAN Weight Management (Light Repo + Good WAV Inference)

### Added

- `scripts/download_hifigan_pretrained.py`

### Updated

- `utils/model.py`

### What changed

- If `hifigan/generator_*.pth.tar` is missing but `.zip` exists, code auto-extracts `.zip` before loading vocoder.
- If checkpoint is still missing, code prints a clear instruction to run:
  - `python scripts/download_hifigan_pretrained.py`
- This keeps repo lighter while still supporting high-quality wav inference when needed.
