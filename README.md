# FastSpeech 2 - PyTorch Implementation

This repository is based on `ming024/FastSpeech2` and keeps the original FastSpeech2 architecture.
The clean branch in this workspace adds a Vietnamese training pipeline for the Hugging Face dataset `doof-ferb/infore1_25hours`.

![](./img/model.png)

## Vietnamese Project Docs

Project-specific documentation for the clean Vietnamese pipeline:

- `docs/README.md`
- `docs/en/setup-infore1.md`
- `docs/en/local-train-guide.md`
- `docs/en/mfa-vietnamese-alignment.md`
- `docs/vn/huong-dan-cai-dat-infore1.md`
- `docs/vn/huong-dan-train-local.md`
- `docs/vn/alignment-mfa-tieng-viet.md`

## Clean Repo Purpose

This clean repo is intended for:

- GitHub sharing
- Kaggle training with `kaggle_fastspeech2vn.ipynb`
- reproducible setup without bundling local data artifacts

For Kaggle, use:

- `kaggle_fastspeech2vn.ipynb`
- `requirements-kaggle.txt`

For local usage, see:

- `docs/en/setup-infore1.md`
- `docs/en/local-train-guide.md`

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

For English multi-speaker TTS, run:

```bash
python3 synthesize.py --text "YOUR_DESIRED_TEXT" --speaker_id SPEAKER_ID --restore_step 800000 --mode single -p config/LibriTTS/preprocess.yaml -m config/LibriTTS/model.yaml -t config/LibriTTS/train.yaml
```

## Upstream Training Notes

The original repository supports LJSpeech, AISHELL-3, and LibriTTS.
For the customized Vietnamese InfoRe1 workflow in this clean repo, follow the docs under `docs/`.

## References

- [FastSpeech 2: Fast and High-Quality End-to-End Text to Speech](https://arxiv.org/abs/2006.04558)
- [xcmyz's FastSpeech implementation](https://github.com/xcmyz/FastSpeech)
- [TensorSpeech's FastSpeech 2 implementation](https://github.com/TensorSpeech/TensorflowTTS)
- [rishikksh20's FastSpeech 2 implementation](https://github.com/rishikksh20/FastSpeech2)
