import atexit
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from pyngrok import ngrok


ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = os.environ.get("PYTHON_EXE", sys.executable)
NGROK_AUTHTOKEN = os.environ.get("NGROK_AUTHTOKEN", "")


def start_service(module: str, port: int):
    cmd = [
        PYTHON_EXE,
        "-m",
        "uvicorn",
        module,
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ]
    return subprocess.Popen(cmd, cwd=str(ROOT))


def cleanup(processes):
    for proc in processes:
        if proc and proc.poll() is None:
            proc.terminate()
    ngrok.kill()


def main():
    if not NGROK_AUTHTOKEN:
        raise RuntimeError("NGROK_AUTHTOKEN is missing. Set it in environment variables.")

    ngrok.set_auth_token(NGROK_AUTHTOKEN)

    train_proc = start_service("api.train_infer_api:app", 8001)
    embed_proc = start_service("api.embed_api:app", 8002)
    procs = [train_proc, embed_proc]
    atexit.register(cleanup, procs)

    # Wait a bit for uvicorn to start
    time.sleep(4)
    if train_proc.poll() is not None or embed_proc.poll() is not None:
        raise RuntimeError("One or more API services failed to start.")

    tunnel = ngrok.connect(8001, "http")
    print(tunnel.public_url)
    embed_tunnel = ngrok.connect(8002, "http")
    print(embed_tunnel.public_url)

    # keep-alive loop: keep script alive and restart dead process
    while True:
        if train_proc.poll() is not None:
            print("train/infer API stopped, restarting...")
            train_proc = start_service("api.train_infer_api:app", 8001)
            procs[0] = train_proc
            time.sleep(2)
        if embed_proc.poll() is not None:
            print("embed API stopped, restarting...")
            embed_proc = start_service("api.embed_api:app", 8002)
            procs[1] = embed_proc
            time.sleep(2)
        time.sleep(20)


if __name__ == "__main__":
    main()
