import argparse
import json
import os

import torch
import yaml
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

from utils.model import get_model, get_vocoder, get_param_num
from utils.io import atomic_torch_save, atomic_write_json, utc_timestamp
from utils.tools import to_device, log, synth_one_sample
from model import FastSpeech2Loss
from dataset import Dataset

from evaluate import evaluate

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def create_grad_scaler(use_amp):
    if hasattr(torch, "amp") and hasattr(torch.amp, "GradScaler"):
        return torch.amp.GradScaler("cuda", enabled=use_amp)
    return torch.cuda.amp.GradScaler(enabled=use_amp)


def load_best_checkpoint_records(ckpt_dir):
    metadata_path = os.path.join(ckpt_dir, "best_checkpoints.json")
    if not os.path.exists(metadata_path):
        return [], metadata_path

    with open(metadata_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    records = [
        record
        for record in records
        if os.path.exists(os.path.join(ckpt_dir, record["filename"]))
    ]
    return records, metadata_path


def save_latest_checkpoint(ckpt_dir, step, epoch, score, state):
    os.makedirs(ckpt_dir, exist_ok=True)
    latest_filename = "latest.pth.tar"
    latest_path = os.path.join(ckpt_dir, latest_filename)
    latest_metadata_path = os.path.join(ckpt_dir, "latest_checkpoint.json")

    state = dict(state)
    state["validation_total_loss"] = float(score)
    state["val_loss"] = float(score)
    state["step"] = step
    state["epoch"] = epoch
    state["timestamp"] = utc_timestamp()
    atomic_torch_save(state, latest_path)

    latest_record = {
        "filename": latest_filename,
        "step": step,
        "epoch": epoch,
        "val_loss": float(score),
        "validation_total_loss": float(score),
        "timestamp": state["timestamp"],
    }
    atomic_write_json(latest_record, latest_metadata_path)

    return latest_record


def save_best_checkpoint(ckpt_dir, step, epoch, score, state, keep):
    os.makedirs(ckpt_dir, exist_ok=True)
    records, metadata_path = load_best_checkpoint_records(ckpt_dir)

    filename = "{}.pth.tar".format(step)
    ckpt_path = os.path.join(ckpt_dir, filename)
    state = dict(state)
    state["validation_total_loss"] = float(score)
    state["val_loss"] = float(score)
    state["step"] = step
    state["epoch"] = epoch
    state["timestamp"] = utc_timestamp()
    atomic_torch_save(state, ckpt_path)

    records.append(
        {
            "filename": filename,
            "step": step,
            "epoch": epoch,
            "val_loss": float(score),
            "validation_total_loss": float(score),
            "timestamp": state["timestamp"],
        }
    )
    records.sort(key=lambda record: (record["validation_total_loss"], record["step"]))

    kept = records[:keep]
    kept_names = {record["filename"] for record in kept}
    removed = []
    for record in records[keep:]:
        old_path = os.path.join(ckpt_dir, record["filename"])
        if os.path.exists(old_path):
            os.remove(old_path)
            removed.append(record["filename"])

    atomic_write_json(kept, metadata_path)

    return filename in kept_names, removed


def main(args, configs):
    print("Prepare training ...")

    preprocess_config, model_config, train_config = configs
    accelerator_config = train_config.get("accelerator", {})
    dataloader_config = train_config.get("dataloader", {})

    if device.type == "cuda" and accelerator_config.get("cudnn_benchmark", True):
        torch.backends.cudnn.benchmark = True

    gpu_count = torch.cuda.device_count() if device.type == "cuda" else 0
    use_amp = bool(accelerator_config.get("use_amp", False) and device.type == "cuda")
    scaler = create_grad_scaler(use_amp)

    if gpu_count > 0:
        gpu_names = [torch.cuda.get_device_name(i) for i in range(gpu_count)]
        print("Visible GPUs:", gpu_names)
    print("Using mixed precision:", use_amp)

    dataset = Dataset(
        "train.txt", preprocess_config, train_config, sort=True, drop_last=True
    )
    batch_size = train_config["optimizer"]["batch_size"]
    grad_acc_step = train_config["optimizer"]["grad_acc_step"]
    group_size = dataloader_config.get("group_size", 4)
    assert batch_size * group_size < len(dataset)

    num_workers = dataloader_config.get("num_workers")
    if num_workers is None:
        num_workers = min(4, os.cpu_count() or 1)
    pin_memory = dataloader_config.get("pin_memory", device.type == "cuda")
    persistent_workers = bool(
        dataloader_config.get("persistent_workers", num_workers > 0)
    )
    prefetch_factor = dataloader_config.get("prefetch_factor", 2)

    loader_kwargs = {
        "dataset": dataset,
        "batch_size": batch_size * group_size,
        "shuffle": True,
        "collate_fn": dataset.collate_fn,
        "num_workers": num_workers,
        "pin_memory": pin_memory,
    }
    if num_workers > 0:
        loader_kwargs["persistent_workers"] = persistent_workers
        loader_kwargs["prefetch_factor"] = prefetch_factor

    loader = DataLoader(**loader_kwargs)

    model, optimizer = get_model(args, configs, device, train=True)
    if gpu_count > 1:
        model = nn.DataParallel(model)
        print("DataParallel enabled on {} GPUs".format(gpu_count))
    num_param = get_param_num(model)
    Loss = FastSpeech2Loss(preprocess_config, model_config).to(device)
    print("Number of FastSpeech2 Parameters:", num_param)
    print(
        "Effective global batch per optimizer step:",
        batch_size * grad_acc_step,
    )
    if gpu_count > 1:
        print("Per-GPU micro-batch:", batch_size // gpu_count)

    vocoder = get_vocoder(model_config, device)

    for p in train_config["path"].values():
        os.makedirs(p, exist_ok=True)
    train_log_path = os.path.join(train_config["path"]["log_path"], "train")
    val_log_path = os.path.join(train_config["path"]["log_path"], "val")
    os.makedirs(train_log_path, exist_ok=True)
    os.makedirs(val_log_path, exist_ok=True)
    train_logger = SummaryWriter(train_log_path)
    val_logger = SummaryWriter(val_log_path)

    step = args.restore_step + 1
    epoch = 1
    grad_clip_thresh = train_config["optimizer"]["grad_clip_thresh"]
    total_step = train_config["step"]["total_step"]
    log_step = train_config["step"]["log_step"]
    save_step = train_config["step"]["save_step"]
    synth_step = train_config["step"]["synth_step"]
    val_step = train_config["step"]["val_step"]
    keep_best_ckpts = train_config["step"].get("keep_best_ckpts", 3)
    latest_val_total_loss = None

    optimizer.zero_grad()

    outer_bar = tqdm(total=total_step, desc="Training", position=0)
    outer_bar.n = args.restore_step
    outer_bar.update()

    while True:
        inner_bar = tqdm(total=len(loader), desc="Epoch {}".format(epoch), position=1)
        for batchs in loader:
            for batch in batchs:
                batch = to_device(batch, device)

                with torch.amp.autocast(device_type="cuda", enabled=use_amp):
                    output = model(*(batch[2:]))
                    losses = Loss(batch, output)
                    total_loss = losses[0]

                total_loss = total_loss / grad_acc_step
                if use_amp:
                    scaler.scale(total_loss).backward()
                else:
                    total_loss.backward()

                if step % grad_acc_step == 0:
                    if use_amp:
                        scaler.unscale_(optimizer._optimizer)
                    nn.utils.clip_grad_norm_(model.parameters(), grad_clip_thresh)
                    optimizer.step_and_update_lr(scaler=scaler if use_amp else None)
                    if use_amp:
                        scaler.update()
                    optimizer.zero_grad()

                if step % log_step == 0:
                    losses = [l.item() for l in losses]
                    message1 = "Step {}/{}, ".format(step, total_step)
                    message2 = "Total Loss: {:.4f}, Mel Loss: {:.4f}, Mel PostNet Loss: {:.4f}, Pitch Loss: {:.4f}, Energy Loss: {:.4f}, Duration Loss: {:.4f}".format(
                        *losses
                    )

                    with open(os.path.join(train_log_path, "log.txt"), "a") as f:
                        f.write(message1 + message2 + "\n")

                    outer_bar.write(message1 + message2)
                    log(train_logger, step, losses=losses)

                if step % synth_step == 0:
                    fig, wav_reconstruction, wav_prediction, tag = synth_one_sample(
                        batch,
                        output,
                        vocoder,
                        model_config,
                        preprocess_config,
                    )
                    log(
                        train_logger,
                        fig=fig,
                        tag="Training/step_{}_{}".format(step, tag),
                    )
                    sampling_rate = preprocess_config["preprocessing"]["audio"][
                        "sampling_rate"
                    ]
                    log(
                        train_logger,
                        audio=wav_reconstruction,
                        sampling_rate=sampling_rate,
                        tag="Training/step_{}_{}_reconstructed".format(step, tag),
                    )
                    log(
                        train_logger,
                        audio=wav_prediction,
                        sampling_rate=sampling_rate,
                        tag="Training/step_{}_{}_synthesized".format(step, tag),
                    )

                if step % val_step == 0:
                    model.eval()
                    message, val_losses = evaluate(
                        model, step, configs, val_logger, vocoder
                    )
                    latest_val_total_loss = val_losses[0]
                    with open(os.path.join(val_log_path, "log.txt"), "a") as f:
                        f.write(message + "\n")
                    outer_bar.write(message)
                    model.train()

                if step % save_step == 0:
                    if latest_val_total_loss is None:
                        outer_bar.write(
                            "Skip checkpoint at step {} because no validation loss is available yet.".format(
                                step
                            )
                        )
                    else:
                        model_state = (
                            model.module.state_dict()
                            if isinstance(model, nn.DataParallel)
                            else model.state_dict()
                        )
                        latest_record = save_latest_checkpoint(
                            train_config["path"]["ckpt_path"],
                            step,
                            epoch,
                            latest_val_total_loss,
                            {
                                "model": model_state,
                                "optimizer": optimizer._optimizer.state_dict(),
                            },
                        )
                        kept, removed = save_best_checkpoint(
                            train_config["path"]["ckpt_path"],
                            step,
                            epoch,
                            latest_val_total_loss,
                            {
                                "model": model_state,
                                "optimizer": optimizer._optimizer.state_dict(),
                            },
                            keep_best_ckpts,
                        )
                        if kept:
                            outer_bar.write(
                                "Saved checkpoint {} with validation total loss {:.4f}".format(
                                    step, latest_val_total_loss
                                )
                            )
                        else:
                            outer_bar.write(
                                "Checkpoint {} was pruned immediately; better checkpoints already exist.".format(
                                    step
                                )
                            )
                        if removed:
                            outer_bar.write(
                                "Removed old checkpoints: {}".format(
                                    ", ".join(removed)
                                )
                            )
                        outer_bar.write(
                            "Updated latest checkpoint: {} (step {}, epoch {}, validation total loss {:.4f})".format(
                                latest_record["filename"],
                                latest_record["step"],
                                latest_record["epoch"],
                                latest_record["val_loss"],
                            )
                        )

                if step == total_step:
                    quit()
                step += 1
                outer_bar.update(1)

            inner_bar.update(1)
        epoch += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--restore_step", type=int, default=0)
    parser.add_argument(
        "-p",
        "--preprocess_config",
        type=str,
        required=True,
        help="path to preprocess.yaml",
    )
    parser.add_argument(
        "-m", "--model_config", type=str, required=True, help="path to model.yaml"
    )
    parser.add_argument(
        "-t", "--train_config", type=str, required=True, help="path to train.yaml"
    )
    args = parser.parse_args()

    preprocess_config = yaml.load(
        open(args.preprocess_config, "r"), Loader=yaml.FullLoader
    )
    model_config = yaml.load(open(args.model_config, "r"), Loader=yaml.FullLoader)
    train_config = yaml.load(open(args.train_config, "r"), Loader=yaml.FullLoader)
    configs = (preprocess_config, model_config, train_config)

    main(args, configs)
