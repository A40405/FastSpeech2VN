# Vietnamese MFA Alignment

This document describes the more serious Vietnamese alignment workflow for the clean FastSpeech2 repo.

## Why this path matters

The bootstrap TextGrid path in this repo exists for quick smoke tests only. It divides utterance duration evenly across phone tokens, so it is useful for verifying that the pipeline runs end to end, but it is not a real forced aligner.

If you want better duration targets, phone boundaries, rhythm, and pause placement, use Montreal Forced Aligner (MFA).

## Design choice in this repo

This repo now uses an IPA-style Vietnamese phone inventory defined in `text/vietnamese.py`.
That means the most consistent serious path is:

1. build an IPA-style pronunciation dictionary from the repo's own Vietnamese frontend
2. export MFA-style G2P training data and a normalized word list
3. export a mapping between raw IPA phones and FastSpeech2 text symbols
4. build an MFA corpus from the prepared raw files
5. run `mfa train_g2p` to train a reusable G2P model
6. run `mfa train` to train an MFA acoustic model and export TextGrids
7. run `preprocess.py` on those TextGrids

This keeps MFA labels aligned with the same IPA-style phone symbols that FastSpeech2 training uses in this repo.

## ViMFA-style position

This is closer to a real Vietnamese TTS stack than the old custom token set, because the repo now produces:

- an MFA lexicon
- G2P training data in `word<TAB>phones` format
- a normalized Vietnamese word list
- a symbol map from IPA phones to FastSpeech2 text symbols

It is still a deterministic frontend in this repo, not a separately trained neural G2P model by default.

## New scripts

- `scripts/build_infore1_mfa_assets.py`
- `scripts/run_mfa_train_alignment.py`
- `scripts/train_vietnamese_g2p.py`
- `scripts/prepare_infore1_mfa.ps1`

## Install MFA

Recommended installation:

```powershell
conda install -c conda-forge montreal-forced-aligner
```

Verify installation:

```powershell
mfa version
```

## Step-by-step workflow

### 1) Prepare raw files

```powershell
python .\prepare_align.py .\config\InfoRe1_25hours\preprocess.yaml
```

### 2) Build MFA corpus, lexicon, G2P data, and symbol map

```powershell
python .\scripts\build_infore1_mfa_assets.py --raw-root .\raw_data\InfoRe1 --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict --g2p-train-path .\mfa_assets\infore1_vi_g2p.tsv --wordlist-path .\mfa_assets\infore1_vi.wordlist --symbol-map-path .\mfa_assets\infore1_vi_symbol_map.tsv
```

Expected outputs:

- `mfa_corpus/InfoRe1/.../*.wav`
- `mfa_corpus/InfoRe1/.../*.lab`
- `mfa_assets/infore1_vi.dict`
- `mfa_assets/infore1_vi_g2p.tsv`
- `mfa_assets/infore1_vi.wordlist`
- `mfa_assets/infore1_vi_symbol_map.tsv`

### 3) Train an MFA G2P model

```powershell
python .\scripts\train_vietnamese_g2p.py --mfa mfa --dictionary-path .\mfa_assets\infore1_vi_g2p.tsv --output-model-path .\mfa_assets\infore1_vi_g2p_model.zip --overwrite
```

Expected output:

- `mfa_assets/infore1_vi_g2p_model.zip`

### 4) Train MFA and export TextGrids

```powershell
python .\scripts\run_mfa_train_alignment.py --mfa mfa --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict --output-root .\preprocessed_data\InfoRe1\TextGrid --model-path .\mfa_assets\infore1_vi_acoustic_model.zip --num-jobs 4 --single-speaker --overwrite
```

Expected outputs:

- `preprocessed_data/InfoRe1/TextGrid/.../*.TextGrid`
- `mfa_assets/infore1_vi_acoustic_model.zip`

### 5) Preprocess acoustic features

```powershell
python .\preprocess.py .\config\InfoRe1_25hours\preprocess.yaml
```

### 6) Train FastSpeech2

```powershell
python .\train.py -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

## One-command version

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1_mfa.ps1
```

This one-command path now also exports the lexicon, G2P data, word list, symbol map, and trains the G2P model before running MFA acoustic alignment.

## When to use this path

Use MFA when:

- you care about more realistic phone boundaries
- you want better duration supervision
- you want a more serious Vietnamese TTS training run

Use bootstrap only when:

- you want a fast smoke test
- you are debugging preprocessing or training setup
- you do not want to install MFA yet

## Important note

This clean repo does not directly use the official pretrained Vietnamese MFA acoustic model.
Instead, it trains MFA on the repo's own IPA-style pronunciation inventory so the labels remain compatible with FastSpeech2 training.
