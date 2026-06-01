# Ngrok Services (8001 / 8002)

This setup starts:

- `train/infer API` on port `8001`
- `embed API` on port `8002`
- two ngrok tunnels and prints public URLs
- keep-alive loop with auto-restart if a service process exits

## Files

- `api/train_infer_api.py`
- `api/embed_api.py`
- `scripts/start_ngrok_services.py`

## Install

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' -m pip install -r .\requirements-llama_gpu.txt
```

## Run

Set your ngrok token in environment variable:

```powershell
$env:NGROK_AUTHTOKEN="YOUR_NGROK_TOKEN"
$env:PYTHON_EXE="D:\Anaconda\envs\llama_gpu\python.exe"
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\start_ngrok_services.py
```

The script prints 2 lines:

- line 1: public URL for `8001` (`train/infer API`)
- line 2: public URL for `8002` (`embed API`)

## Endpoints

### Train/Infer API (port 8001)

- `GET /health`
- `GET /train/status`
- `POST /train/start`
- `POST /train/stop`
- `POST /infer`

Example `train/start` body:

```json
{
  "preprocess_config": "config/InfoRe1_25hours/preprocess.yaml",
  "model_config": "config/InfoRe1_25hours/model.yaml",
  "train_config": "config/InfoRe1_25hours/train.yaml",
  "restore_step": 0
}
```

Example `infer` body:

```json
{
  "text": "xin chao ban",
  "restore_step": 10000
}
```

### Embed API (port 8002)

- `GET /health`
- `POST /embed`

Example body:

```json
{
  "text": "xin chao ban",
  "dim": 256
}
```
