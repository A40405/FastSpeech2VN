import hashlib
from typing import List

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from text.vietnamese import phonemize_text


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

    tokens = phonemize_text(text)
    embedding = build_embedding(tokens, req.dim)
    return {
        "tokens": tokens,
        "dim": req.dim,
        "embedding": embedding,
    }
