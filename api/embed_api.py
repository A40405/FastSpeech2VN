import hashlib
import os
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from text.vietnamese import (
    PAUSE_WORD,
    normalize_text,
    text_to_training_units,
    word_to_phoneme_tokens,
)
from utils.lexicon import read_mfa_lexicon


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEXICON_PATH = Path(os.environ.get("EMBED_LEXICON_PATH", ROOT / "mfa_assets" / "infore1_vi.dict"))
DEFAULT_G2P_MODEL_PATH = Path(os.environ.get("EMBED_G2P_MODEL_PATH", ROOT / "mfa_assets" / "infore1_vi_g2p_model.zip"))
DEFAULT_MFA_EXE = os.environ.get("MFA_EXE", "mfa")

app = FastAPI(title="Vietnamese Embed API", version="1.0")


class EmbedRequest(BaseModel):
    text: str
    dim: int = 256


def _hash_to_index(token: str, dim: int) -> int:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "little") % dim


def build_embedding(tokens: List[str], dim: int) -> List[float]:
    vec = np.zeros(dim, dtype=np.float32)
    for token in tokens:
        vec[_hash_to_index(token, dim)] += 1.0
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


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


def vietnamese_tokens(text: str) -> List[str]:
    words = [unit for unit in text_to_training_units(text) if unit != PAUSE_WORD]
    lexicon = read_lexicon(DEFAULT_LEXICON_PATH)

    unknown_words = []
    for word in words:
        lookup = word.lower()
        if lexicon and lookup not in lexicon:
            unknown_words.append(lookup)

    g2p_pronunciations = {}
    if unknown_words:
        g2p_pronunciations = run_mfa_g2p(
            tuple(sorted(set(unknown_words))),
            str(DEFAULT_G2P_MODEL_PATH),
            DEFAULT_MFA_EXE,
        )

    tokens: List[str] = []
    for word in text_to_training_units(text):
        if word == PAUSE_WORD:
            tokens.append("sp")
            continue

        lookup = word.lower()
        if lookup in lexicon:
            word_tokens = lexicon[lookup]
        elif lookup in g2p_pronunciations:
            word_tokens = g2p_pronunciations[lookup]
        else:
            word_tokens = word_to_phoneme_tokens(normalize_text(word))

        tokens.extend(word_tokens)

    return tokens or ["spn"]


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/embed")
def embed(req: EmbedRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    if req.dim < 32 or req.dim > 2048:
        raise HTTPException(status_code=400, detail="dim must be in [32, 2048]")

    tokens = vietnamese_tokens(text)
    embedding = build_embedding(tokens, req.dim)
    return {
        "tokens": tokens,
        "dim": req.dim,
        "embedding": embedding,
    }
