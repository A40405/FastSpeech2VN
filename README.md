# FastSpeech 2 - PyTorch Implementation

This repository is based on `ming024/FastSpeech2` and keeps the original FastSpeech2 architecture.
The clean branch in this workspace adds a Vietnamese training pipeline for the Hugging Face dataset `doof-ferb/infore1_25hours`.

The Vietnamese frontend now uses an IPA-style phone inventory so the text frontend, MFA lexicon, alignment labels, runtime OOV handling, and demo packaging are closer to a real Vietnamese TTS pipeline such as ViMFA.

![](./img/model.png)

## Vietnamese Project Docs

Project-specific documentation for the clean Vietnamese pipeline:

- `docs/README.md`
- `docs/en/infore1-setup.md`
- `docs/en/infore1-local-train-guide.md`
- `docs/en/mfa-vietnamese-alignment.md`
- `docs/en/vietnamese-pipeline-changes.md`
- `docs/en/ngrok-services.md`
- `docs/en/infore1-vietnamese-demo.md`
- `docs/vn/infore1-cai-dat.md`
- `docs/vn/infore1-train-local.md`
- `docs/vn/alignment-mfa-tieng-viet.md`
- `docs/vn/thay-doi-pipeline-tieng-viet.md`
- `docs/vn/dich-vu-ngrok.md`
- `docs/vn/infore1-demo-tieng-viet.md`

## Clean Repo Purpose

This clean repo is intended for:

- GitHub sharing
- reproducible setup without bundling local data artifacts

For Kaggle, keep the notebook outside the repo and use `requirements-kaggle.txt`.
The GitHub repo itself does not bundle Kaggle notebooks.

For local usage, see:

- `docs/en/infore1-setup.md`
- `docs/en/infore1-local-train-guide.md`

## Vietnamese Frontend Notes

The repo does not use the old `on_ / v_ / cod_ / tone_` token set anymore.
It now uses IPA-style Vietnamese tokens produced by `text/vietnamese.py`.

In addition to `.phones` generation, the repo now exports:

- an MFA lexicon: `mfa_assets/infore1_vi.dict`
- MFA-style G2P training data: `mfa_assets/infore1_vi_g2p.tsv`
- an IPA-to-FastSpeech2 symbol map: `mfa_assets/infore1_vi_symbol_map.tsv`

The runtime inference order is lexicon first, trained G2P for OOV words second, and rule-based phonemization only as the final fallback.

This makes the pipeline closer to ViMFA-style organization, while still keeping FastSpeech2 and the repo's own Vietnamese frontend self-contained.

## Upstream FastSpeech2 Notes

The rest of the codebase still follows the original FastSpeech2 implementation style from upstream.
If you need project-specific Vietnamese workflow details, prefer the documentation under `docs/` instead of relying only on the upstream-style sections below.

## Quickstart

Install Python dependencies with:

```bash
pip3 install -r requirements.txt
```

## Upstream Inference Examples

You have to download the [pretrained models](https://drive.google.com/drive/folders/1DOhZGlTLMbbAAFZmZGDdc77kz1PloS7F?usp=sharing) and put them in `output/ckpt/LJSpeech/`, `output/ckpt/AISHELL3`, or `output/ckpt/LibriTTS/`.

For English single-speaker TTS, run:

```bash
python3 synthesize.py --text "YOUR_DESIRED_TEXT" --restore_step 900000 --mode single -p config/LJSpeech/preprocess.yaml -m config/LJSpeech/model.yaml -t config/LJSpeech/train.yaml
```

For Mandarin multi-speaker TTS, run:

```bash
python3 synthesize.py --text "大家好" --speaker_id SPEAKER_ID --restore_step 600000 --mode single -p config/AISHELL3/preprocess.yaml -m config/AISHELL3/model.yaml -t config/AISHELL3/train.yaml
```
