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
- `mfa_assets/phoneset_report.json`
- `preprocessed_data/InfoRe1/TextGrid`
- `preprocessed_data/InfoRe1/alignment_validation_report.json`

## Why this is still not a full ViMFA clone

The repo now follows the same practical structure as ViMFA:

- IPA-style Vietnamese lexicon
- G2P training data export
- MFA alignment assets
- reusable word list and symbol mapping

However, it is still not a full copy of the ViMFA repository resources:

- the frontend remains deterministic inside this repo
- the G2P model is trained from the exported IPA pronunciation dictionary rather than being copied from ViMFA
- the acoustic alignment model is trained in the repo workflow rather than bundled from ViMFA
- ASCII abbreviations and letter-by-letter tokens fall back to a deterministic spelled-out pronunciation instead of collapsing to `spn`, which improves coverage for items like `TP`, `HCM`, and `UBND`

So the project is ViMFA-inspired and structurally closer to a real Vietnamese TTS stack, but it is still self-contained.

## Alignment and inference order

For Vietnamese inference, the runtime now prefers:

1. lexicon lookup for known words
2. trained G2P model for OOV words
3. deterministic rule-based phonemizer as fallback

That same philosophy is reflected in the full alignment flow.

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
$env:PYTHON_EXE = "python"
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1 -PythonExe $env:PYTHON_EXE -MfaExe "mfa"
```

That wrapper delegates to `scripts/prepare_infore1_mfa.ps1`, which runs the full MFA pipeline including G2P training.

If you want to run the alignment stage manually, the two key commands are:

```powershell
python .\scripts\build_infore1_mfa_assets.py --raw-root .\raw_data\InfoRe1 --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict --g2p-train-path .\mfa_assets\infore1_vi_g2p.tsv --wordlist-path .\mfa_assets\infore1_vi.wordlist --symbol-map-path .\mfa_assets\infore1_vi_symbol_map.tsv
```

```powershell
python .\scripts\train_vietnamese_g2p.py --mfa mfa --dictionary-path .\mfa_assets\infore1_vi.dict --output-model-path .\mfa_assets\infore1_vi_g2p_model.zip --overwrite
```

```powershell
python .\scripts\run_mfa_train_alignment.py --mfa mfa --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict --output-root .\preprocessed_data\InfoRe1\TextGrid --model-path .\mfa_assets\infore1_vi_acoustic_model.zip --num-jobs 4 --single-speaker --overwrite
```

Before preprocessing, also run:

```powershell
python .\scripts\validate_alignment.py --config .\config\InfoRe1_25hours\preprocess.yaml
python .\scripts\check_phoneset.py --config .\config\InfoRe1_25hours\preprocess.yaml
```

The two reports worth checking are:

- `preprocessed_data/InfoRe1/alignment_validation_report.json`
- `mfa_assets/phoneset_report.json`

## Notes for quality

- Better alignment quality usually means better duration targets for FastSpeech2.
- The repo now repairs recoverable zero-duration alignments during preprocess, but every detected and repaired issue is still logged into the JSON reports.
- When rebuilding `dict` and `g2p.tsv`, the repo injects a small set of synthetic coverage seeds for rare frontend-only IPA symbols so the declared phoneset stays aligned end to end.
- The generated `wordlist` now follows the augmented lexicon so the MFA word list and pronunciation dictionary stay in sync.
- If `TextGrid` already exists, you can skip rerunning the MFA stage.
- The repo is designed so the clean Git version stays shareable and reproducible.
