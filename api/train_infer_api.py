import os
import shutil
import subprocess
import tempfile
import threading
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from text.vietnamese import (
    PAUSE_WORD,
    normalize_text,
    text_to_training_units,
    word_to_phoneme_tokens,
)
from utils.lexicon import read_mfa_lexicon


ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = os.environ.get("PYTHON_EXE", "python")
ENABLE_DEBUG_API = os.environ.get("ENABLE_DEBUG_API", "0").lower() in {"1", "true", "yes", "on"}

app = FastAPI(title="FastSpeech2 Train/Infer API", version="1.0")

_train_proc: Optional[subprocess.Popen] = None
_train_lock = threading.Lock()


class TrainRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    preprocess_config: str = "config/InfoRe1_25hours/preprocess.yaml"
    model_cfg: str = Field(
        default="config/InfoRe1_25hours/model.yaml", alias="model_config"
    )
    train_config: str = "config/InfoRe1_25hours/train.yaml"
    restore_step: int = 0


class InferRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    text: str
    restore_step: int
    preprocess_config: str = "config/InfoRe1_25hours/preprocess.yaml"
    model_cfg: str = Field(
        default="config/InfoRe1_25hours/model.yaml", alias="model_config"
    )
    train_config: str = "config/InfoRe1_25hours/train.yaml"
    speaker_id: int = 0
    pitch_control: float = 1.0
    energy_control: float = 1.0
    duration_control: float = 1.0
    include_frontend_debug: bool = True


class DebugRequest(BaseModel):
    text: str
    preprocess_config: str = "config/InfoRe1_25hours/preprocess.yaml"


def resolve_config_path(config_path: str) -> Path:
    path = Path(config_path)
    if path.is_absolute():
        return path
    return ROOT / path


def load_yaml_config(config_path: str) -> Dict:
    path = resolve_config_path(config_path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader) or {}


def read_lexicon(lex_path: Path) -> Dict[str, List[str]]:
    return read_mfa_lexicon(lex_path)


def resolve_executable(executable: str) -> str:
    executable_path = Path(executable)
    if executable_path.is_file():
        return str(executable_path.resolve())
    discovered = shutil.which(executable)
    if discovered:
        return discovered
    return executable


@lru_cache(maxsize=32)
def run_mfa_g2p(word_tuple, g2p_model_path, mfa_executable):
    g2p_model = Path(g2p_model_path)
    if not g2p_model.exists():
        return {}

    input_words = [word for word in word_tuple if word]
    if not input_words:
        return {}

    resolved_mfa = resolve_executable(mfa_executable)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        input_path = tmpdir / "oovs.txt"
        output_path = tmpdir / "oovs.dict"
        input_path.write_text("\n".join(input_words) + "\n", encoding="utf-8")

        command = [
            resolved_mfa,
            "g2p",
            str(input_path),
            str(g2p_model),
            str(output_path),
            "--clean",
            "--overwrite",
        ]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode != 0 or not output_path.exists():
            return {}

        return read_lexicon(output_path)


def build_vietnamese_frontend_debug(text: str, preprocess_config: Dict) -> Dict:
    path_config = preprocess_config.get("path", {})
    lexicon_path = path_config.get("lexicon_path")
    g2p_model_path = path_config.get("g2p_model_path")
    mfa_executable = path_config.get("mfa_executable", "mfa")

    lexicon = {}
    if lexicon_path:
        resolved_lexicon = resolve_config_path(lexicon_path)
        lexicon = read_lexicon(resolved_lexicon)

    words = [unit for unit in text_to_training_units(text) if unit != PAUSE_WORD]
    unknown_words = []
    for word in words:
        lookup = word.lower()
        if lexicon and lookup not in lexicon:
            unknown_words.append(lookup)

    g2p_pronunciations = {}
    if unknown_words and g2p_model_path:
        resolved_g2p = resolve_config_path(g2p_model_path)
        if resolved_g2p.exists():
            g2p_pronunciations = run_mfa_g2p(
                tuple(sorted(set(unknown_words))),
                str(resolved_g2p),
                mfa_executable,
            )

    word_entries = []
    token_entries = []
    final_tokens = []

    for word in text_to_training_units(text):
        if word == PAUSE_WORD:
            token_entries.append({"word": word, "token": "sp", "source": "punctuation"})
            final_tokens.append("sp")
            continue

        lookup = word.lower()
        if lookup in lexicon:
            source = "lexicon"
            word_tokens = lexicon[lookup]
        elif lookup in g2p_pronunciations:
            source = "g2p"
            word_tokens = g2p_pronunciations[lookup]
        else:
            source = "rule"
            word_tokens = word_to_phoneme_tokens(normalize_text(word))

        word_entries.append({"word": word, "source": source, "tokens": word_tokens})
        for token in word_tokens:
            token_entries.append({"word": word, "token": token, "source": source})
            final_tokens.append(token)

    if not final_tokens:
        final_tokens = ["spn"]

    return {
        "text": text,
        "words": words,
        "entries": word_entries,
        "token_entries": token_entries,
        "tokens": final_tokens,
        "lexicon_path": str(resolve_config_path(lexicon_path)) if lexicon_path else None,
        "g2p_model_path": str(resolve_config_path(g2p_model_path)) if g2p_model_path else None,
        "sources": {
            "lexicon": bool(lexicon),
            "g2p_model": bool(g2p_model_path and resolve_config_path(g2p_model_path).exists()),
        },
    }


@app.get("/health")
def health():
    return {"ok": True, "debug_api_enabled": ENABLE_DEBUG_API}


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
            req.model_cfg,
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

    frontend_debug = None
    if req.include_frontend_debug:
        preprocess_config = load_yaml_config(req.preprocess_config)
        if preprocess_config:
            frontend_debug = build_vietnamese_frontend_debug(req.text, preprocess_config)

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
        req.model_cfg,
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

    response = {"ok": True, "stdout_tail": proc.stdout[-1000:]}
    if frontend_debug is not None:
        response["frontend_debug"] = frontend_debug
    return response


@app.post("/infer/debug")
def infer_debug(req: DebugRequest):
    if not ENABLE_DEBUG_API:
        raise HTTPException(status_code=404, detail="Debug API is disabled in this environment")
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    preprocess_config = load_yaml_config(req.preprocess_config)
    if not preprocess_config:
        raise HTTPException(status_code=400, detail="Invalid preprocess config")

    return {"ok": True, "frontend_debug": build_vietnamese_frontend_debug(text, preprocess_config)}
