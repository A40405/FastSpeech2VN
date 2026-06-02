import argparse
import os

import torch
import yaml
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

from utils.model import get_model, get_vocoder, get_param_num
from utils.tools import to_device, log, synth_one_sample
from model import FastSpeech2Loss
from dataset import Dataset

from evaluate import evaluate

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def main(args, configs):
    print("Prepare training ...")

    preprocess_config, model_config, train_config = configs
    accelerator_config = train_config.get("accelerator", {})
    dataloader_config = train_config.get("dataloader", {})

    if device.type == "cuda" and accelerator_config.get("cudnn_benchmark", True):
        torch.backends.cudnn.benchmark = True

    gpu_count = torch.cuda.device_count() if device.type == "cuda" else 0
    use_amp = bool(accelerator_config.get("use_amp", False) and device.type == "cuda")
    scaler = GradScaler(enabled=use_amp)

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

    optimizer.zero_grad()

    outer_bar = tqdm(total=total_step, desc="Training", position=0)
    outer_bar.n = args.restore_step
    outer_bar.update()

    while True:
        inner_bar = tqdm(total=len(loader), desc="Epoch {}".format(epoch), position=1)
        for batchs in loader:
            for batch in batchs:
                batch = to_device(batch, device)

                with autocast(enabled=use_amp):
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
                    message = evaluate(model, step, configs, val_logger, vocoder)
                    with open(os.path.join(val_log_path, "log.txt"), "a") as f:
                        f.write(message + "\n")
                    outer_bar.write(message)
                    model.train()

                if step % save_step == 0:
                    model_state = model.module.state_dict() if isinstance(model, nn.DataParallel) else model.state_dict()
                    torch.save(
                        {
                            "model": model_state,
                            "optimizer": optimizer._optimizer.state_dict(),
                        },
                        os.path.join(
                            train_config["path"]["ckpt_path"],
                            "{}.pth.tar".format(step),
                        ),
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

