import os
import subprocess
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = os.environ.get("PYTHON_EXE", "python")

app = FastAPI(title="FastSpeech2 Train/Infer API", version="1.0")

_train_proc: Optional[subprocess.Popen] = None
_train_lock = threading.Lock()


class TrainRequest(BaseModel):
    preprocess_config: str = "config/InfoRe1_25hours/preprocess.yaml"
    model_config: str = "config/InfoRe1_25hours/model.yaml"
    train_config: str = "config/InfoRe1_25hours/train.yaml"
    restore_step: int = 0


class InferRequest(BaseModel):
    text: str
    restore_step: int
    preprocess_config: str = "config/InfoRe1_25hours/preprocess.yaml"
    model_config: str = "config/InfoRe1_25hours/model.yaml"
    train_config: str = "config/InfoRe1_25hours/train.yaml"
    speaker_id: int = 0
    pitch_control: float = 1.0
    energy_control: float = 1.0
    duration_control: float = 1.0


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/train/start")
def start_train(req: TrainRequest):
    global _train_proc
    with _train_lock:
        if _train_proc and _train_proc.poll() is None:
            raise HTTPException(status_code=409, detail="Training is already running")

        cmd = [
            PYTHON_EXE,
            "train.py",
            "-p",
            req.preprocess_config,
            "-m",
            req.model_config,
            "-t",
            req.train_config,
        ]
        if req.restore_step > 0:
            cmd.extend(["--restore_step", str(req.restore_step)])

        _train_proc = subprocess.Popen(cmd, cwd=str(ROOT))
        return {"started": True, "pid": _train_proc.pid, "cmd": cmd}


@app.post("/train/stop")
def stop_train():
    global _train_proc
    with _train_lock:
        if not _train_proc or _train_proc.poll() is not None:
            return {"stopped": False, "message": "No running training process"}
        _train_proc.terminate()
        return {"stopped": True, "pid": _train_proc.pid}


@app.get("/train/status")
def train_status():
    if not _train_proc:
        return {"running": False}
    code = _train_proc.poll()
    return {"running": code is None, "pid": _train_proc.pid, "returncode": code}


@app.post("/infer")
def infer(req: InferRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    cmd = [
        PYTHON_EXE,
        "synthesize.py",
        "--restore_step",
        str(req.restore_step),
        "--mode",
        "single",
        "--text",
        req.text,
        "--speaker_id",
        str(req.speaker_id),
        "-p",
        req.preprocess_config,
        "-m",
        req.model_config,
        "-t",
        req.train_config,
        "--pitch_control",
        str(req.pitch_control),
        "--energy_control",
        str(req.energy_control),
        "--duration_control",
        str(req.duration_control),
    ]

    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={"error": "synthesize failed", "stderr": proc.stderr[-3000:]},
        )

    return {"ok": True, "stdout_tail": proc.stdout[-1000:]}
