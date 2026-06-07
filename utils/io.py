import json
import os
import tempfile
from datetime import datetime, timezone

import torch


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def _atomic_tmp_path(path):
    directory = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(
        dir=directory,
        prefix=os.path.basename(path) + ".",
        suffix=".tmp",
    )
    os.close(fd)
    return tmp_path


def atomic_write_json(data, path):
    tmp_path = _atomic_tmp_path(path)
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def atomic_torch_save(obj, path):
    tmp_path = _atomic_tmp_path(path)
    try:
        torch.save(obj, tmp_path)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
