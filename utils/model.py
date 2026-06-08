import os
import json
import zipfile
import sys
from pathlib import Path

import torch
import numpy as np

import hifigan
from model import FastSpeech2, ScheduledOptim


def patch_numpy_compat():
    # Some checkpoints were saved in environments that serialized numpy internals
    # under `numpy._core.*`, while older local envs may only expose `numpy.core.*`.
    if "numpy._core" not in sys.modules:
        import numpy.core as numpy_core

        sys.modules["numpy._core"] = numpy_core

    if "numpy._core.multiarray" not in sys.modules:
        import numpy.core.multiarray as numpy_core_multiarray

        sys.modules["numpy._core.multiarray"] = numpy_core_multiarray


def load_torch_checkpoint(path, map_location=None):
    # FastSpeech2 checkpoints in this repo store optimizer/model dicts created
    # before PyTorch changed torch.load default to weights_only=True.
    patch_numpy_compat()
    return torch.load(path, map_location=map_location, weights_only=False)


def _numeric_checkpoint_candidates(ckpt_dir):
    return sorted(
        (
            path
            for path in ckpt_dir.glob("*.pth.tar")
            if path.name.split(".")[0].isdigit()
        ),
        key=lambda path: int(path.name.split(".")[0]),
    )


def resolve_restore_checkpoint(ckpt_root, restore_step):
    ckpt_dir = Path(ckpt_root)

    if restore_step in (None, "", 0):
        candidates = _numeric_checkpoint_candidates(ckpt_dir)
        if not candidates:
            raise FileNotFoundError(f"Khong tim thay checkpoint nao trong: {ckpt_dir}")
        resolved_path = candidates[-1]
        return resolved_path, int(resolved_path.name.split(".")[0])

    if isinstance(restore_step, str) and restore_step.lower() == "latest":
        latest_path = ckpt_dir / "latest.pth.tar"
        if latest_path.exists():
            return latest_path, None

        latest_meta_path = ckpt_dir / "latest_checkpoint.json"
        if latest_meta_path.exists():
            latest_meta = json.loads(latest_meta_path.read_text(encoding="utf-8"))
            meta_step = latest_meta.get("step")
            if isinstance(meta_step, int):
                numbered_path = ckpt_dir / f"{meta_step}.pth.tar"
                if numbered_path.exists():
                    return numbered_path, meta_step

        candidates = _numeric_checkpoint_candidates(ckpt_dir)
        if not candidates:
            raise FileNotFoundError(
                f"Khong tim thay latest.pth.tar hoac checkpoint so trong: {ckpt_dir}"
            )
        resolved_path = candidates[-1]
        return resolved_path, int(resolved_path.name.split(".")[0])

    resolved_path = ckpt_dir / f"{restore_step}.pth.tar"
    if not resolved_path.exists():
        raise FileNotFoundError(f"Khong tim thay checkpoint: {resolved_path}")
    return resolved_path, int(restore_step)


def get_model(args, configs, device, train=False):
    (preprocess_config, model_config, train_config) = configs

    model = FastSpeech2(preprocess_config, model_config).to(device)
    resolved_restore_step = args.restore_step
    if args.restore_step:
        ckpt_path, inferred_step = resolve_restore_checkpoint(
            train_config["path"]["ckpt_path"], args.restore_step
        )
        ckpt = load_torch_checkpoint(ckpt_path, map_location=device)
        model.load_state_dict(ckpt["model"])
        resolved_restore_step = (
            ckpt.get("step")
            or ckpt.get("global_step")
            or inferred_step
            or args.restore_step
        )

    if train:
        scheduled_optim = ScheduledOptim(
            model, train_config, model_config, resolved_restore_step
        )
        if args.restore_step:
            scheduled_optim.load_state_dict(ckpt["optimizer"])
        model.train()
        return model, scheduled_optim

    model.eval()
    model.requires_grad_ = False
    return model


def get_param_num(model):
    num_param = sum(param.numel() for param in model.parameters())
    return num_param


def get_vocoder(config, device):
    name = config["vocoder"]["model"]
    speaker = config["vocoder"]["speaker"]

    if not name:
        return None

    if name == "MelGAN":
        if speaker == "LJSpeech":
            vocoder = torch.hub.load(
                "descriptinc/melgan-neurips", "load_melgan", "linda_johnson"
            )
        elif speaker == "universal":
            vocoder = torch.hub.load(
                "descriptinc/melgan-neurips", "load_melgan", "multi_speaker"
            )
        vocoder.mel2wav.eval()
        vocoder.mel2wav.to(device)
    elif name == "HiFi-GAN":
        if not os.path.exists("hifigan/config.json"):
            return None
        with open("hifigan/config.json", "r") as f:
            config = json.load(f)
        config = hifigan.AttrDict(config)
        vocoder = hifigan.Generator(config)
        if speaker == "LJSpeech":
            ckpt_path = "hifigan/generator_LJSpeech.pth.tar"
        elif speaker == "universal":
            ckpt_path = "hifigan/generator_universal.pth.tar"
        else:
            return None
        zip_ckpt_path = ckpt_path + ".zip"
        if not os.path.exists(ckpt_path) and os.path.exists(zip_ckpt_path):
            with zipfile.ZipFile(zip_ckpt_path, "r") as zf:
                zf.extractall("hifigan")
        if not os.path.exists(ckpt_path):
            print(
                "[HiFi-GAN] Missing checkpoint: {}. "
                "Run `python scripts/download_hifigan_pretrained.py` to download."
                .format(ckpt_path)
            )
            return None
        ckpt = load_torch_checkpoint(ckpt_path, map_location=device)
        vocoder.load_state_dict(ckpt["generator"])
        vocoder.eval()
        vocoder.remove_weight_norm()
        vocoder.to(device)
    else:
        return None

    return vocoder


def vocoder_infer(mels, vocoder, model_config, preprocess_config, lengths=None):
    name = model_config["vocoder"]["model"]
    with torch.no_grad():
        if name == "MelGAN":
            wavs = vocoder.inverse(mels / np.log(10))
        elif name == "HiFi-GAN":
            wavs = vocoder(mels.float()).squeeze(1)

    wavs = (
        wavs.cpu().numpy()
        * preprocess_config["preprocessing"]["audio"]["max_wav_value"]
    ).astype("int16")
    wavs = [wav for wav in wavs]

    for i in range(len(mels)):
        if lengths is not None:
            wavs[i] = wavs[i][: lengths[i]]

    return wavs
