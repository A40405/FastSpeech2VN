# Vietnamese MFA Alignment

This guide describes the full Vietnamese alignment path used in the clean repo.

## Core idea

The repo now keeps a ViMFA-inspired IPA-style frontend and uses MFA for alignment.
The recommended path is the full pipeline, not a bootstrap approximation.

## What the pipeline produces

- `mfa_assets/infore1_vi.dict`
- `mfa_assets/infore1_vi_g2p.tsv`
- `mfa_assets/infore1_vi.wordlist`
- `mfa_assets/infore1_vi_symbol_map.tsv`
- `mfa_assets/infore1_vi_g2p_model.zip`
- `preprocessed_data/InfoRe1/TextGrid`

## Why this is still not a full ViMFA clone

The repo now follows the same practical structure as ViMFA:

- IPA-style Vietnamese lexicon
- G2P training data export
- MFA alignment assets
- reusable word list and symbol mapping

However, it is still not a full copy of the ViMFA repository resources:

- the frontend remains deterministic and rule-based inside this repo
- the G2P model is trained from the exported IPA lexicon data rather than being copied from ViMFA
- the acoustic alignment model is trained in the repo workflow rather than bundled from ViMFA

So the project is ViMFA-inspired and structurally closer to a real Vietnamese TTS stack, but it is still self-contained.

## Full alignment flow

1. download the dataset
2. prepare raw audio/text files
3. export MFA assets and the G2P training set
4. train the MFA G2P model
5. train the MFA acoustic aligner
6. export `TextGrid`
7. preprocess FastSpeech2 features
8. train FastSpeech2

## One-command local run

Use the full pipeline wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1
```

That wrapper now calls the full MFA pipeline, including G2P training.

If you want to run the alignment stage manually, the two key commands are:

```powershell
python .\scripts\train_vietnamese_g2p.py --mfa mfa --dictionary-path .\mfa_assets\infore1_vi_g2p.tsv --output-model-path .\mfa_assets\infore1_vi_g2p_model.zip --overwrite
```

```powershell
python .\scripts\run_mfa_train_alignment.py --mfa mfa --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict --output-root .\preprocessed_data\InfoRe1\TextGrid --model-path .\mfa_assets\infore1_vi_acoustic_model.zip --num-jobs 4 --single-speaker --overwrite
```

## Notes for quality

- Better alignment quality usually means better duration targets for FastSpeech2.
- If `TextGrid` already exists, you can skip rerunning the MFA stage.
- The repo is designed so the clean Git version stays shareable and reproducible.
