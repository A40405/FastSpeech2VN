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

## When you need this

Use ngrok services only if you want to call the repo from outside the current machine or notebook session.

If you only need preprocess, train, or local inference, you do not need this part.
