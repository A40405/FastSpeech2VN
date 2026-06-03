# Dịch vụ ngrok

Tài liệu này mô tả lớp dịch vụ từ xa tùy chọn trong repo.

## Nó dùng để làm gì

Thiết lập này sẽ khởi động:

- train/infer API ở cổng `8001`
- embed API ở cổng `8002`
- hai ngrok tunnel để gọi các API đó từ bên ngoài máy hiện tại
- vòng keep-alive để tự khởi động lại service nếu process thoát bất thường

## File liên quan

- `api/train_infer_api.py`
- `api/embed_api.py`
- `scripts/start_ngrok_services.py`

## Cài đặt

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' -m pip install -r .\requirements-llama_gpu.txt
```

## Chạy

Thiết lập ngrok token và đường dẫn Python:

```powershell
$env:NGROK_AUTHTOKEN="YOUR_NGROK_TOKEN"
$env:PYTHON_EXE="D:\Anaconda\envs\llama_gpu\python.exe"
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\start_ngrok_services.py
```

Script sẽ in ra hai public URL:

- URL cho train/infer API ở `8001`
- URL cho embed API ở `8002`

## Endpoint debug frontend tiếng Việt

`api/train_infer_api.py` còn có một endpoint debug được bật bằng cờ môi trường:

```powershell
$env:ENABLE_DEBUG_API="1"
```

Endpoint này:

- `POST /infer/debug`

Nó chỉ trả về debug frontend, không sinh WAV, nên rất tiện để kiểm tra từng từ được lấy từ lexicon, từ G2P model hay từ fallback rule-based.

### Ví dụ request

```json
{
  "text": "xin chao abc",
  "preprocess_config": "config/InfoRe1_25hours/preprocess.yaml"
}
```

### Ví dụ response

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

Nếu không bật `ENABLE_DEBUG_API` thì endpoint sẽ trả `404`.

## Khi nào cần phần này

Chỉ dùng ngrok services nếu bạn muốn gọi repo từ bên ngoài máy hiện tại hoặc từ ngoài phiên notebook.

Nếu bạn chỉ cần preprocess, train, hoặc infer local thì không cần phần này.
