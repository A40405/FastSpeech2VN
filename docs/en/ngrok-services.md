# Ngrok Services

These docs describe the optional remote service layer in this repo.

## What it does

This setup starts:

- a train/infer API on port `8001`
- an embed API on port `8002`
- two ngrok tunnels so those APIs can be reached from outside the current machine
- a keep-alive loop that restarts services if they exit unexpectedly

## Related files

- `api/train_infer_api.py`
- `api/embed_api.py`
- `scripts/start_ngrok_services.py`

## Install

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' -m pip install -r .\requirements-llama_gpu.txt
```

## Run

Set the ngrok token and Python path:

```powershell
$env:NGROK_AUTHTOKEN="YOUR_NGROK_TOKEN"
$env:PYTHON_EXE="D:\Anaconda\envs\llama_gpu\python.exe"
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\start_ngrok_services.py
```

The script prints two public URLs:

- URL for the train/infer API on `8001`
- URL for the embed API on `8002`

## Debug endpoint for Vietnamese frontend

`api/train_infer_api.py` also exposes a gated debug endpoint:

- `POST /infer/debug`

This endpoint is only enabled when:

```powershell
$env:ENABLE_DEBUG_API="1"
```

It returns the frontend breakdown without synthesizing WAV, so it is useful for checking whether each word came from the lexicon, the trained G2P model, or the rule-based fallback.

### Example request

```json
{
  "text": "xin chao abc",
  "preprocess_config": "config/InfoRe1_25hours/preprocess.yaml"
}
```

### Example response

```json
{
  "ok": true,
  "frontend_debug": {
    "text": "xin chao abc",
    "words": ["xin", "chao", "abc"],
    "entries": [
      {
        "word": "xin",
        "source": "lexicon",
        "tokens": ["..."]
      },
      {
        "word": "abc",
        "source": "g2p",
        "tokens": ["..."]
      }
    ],
    "token_entries": [
      {
        "word": "xin",
        "token": "...",
        "source": "lexicon"
      }
    ],
    "tokens": ["..."],
    "lexicon_path": ".../mfa_assets/infore1_vi.dict",
    "g2p_model_path": ".../mfa_assets/infore1_vi_g2p_model.zip",
    "sources": {
      "lexicon": true,
      "g2p_model": true
    }
  }
}
```

If `ENABLE_DEBUG_API` is not set, the endpoint returns `404`.

## When you need this

Use ngrok services only if you want to call the repo from outside the current machine or notebook session.

If you only need preprocess, train, or local inference, you do not need this part.
