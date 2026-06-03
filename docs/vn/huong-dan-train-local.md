# Hướng dẫn train local

Đây là workflow end-to-end chạy local cho repo clean.

## 1) Cài package

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' -m pip install -r .\requirements-llama_gpu.txt
```

## 2) Chạy toàn bộ pipeline InfoRe1

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1
```

Script wrapper này đã chạy luôn:

- tải dataset
- chuẩn bị raw files
- sinh MFA assets
- train G2P model
- chạy MFA alignment
- preprocess FastSpeech2

Tài liệu chi tiết:

- `mfa-vietnamese-alignment.md`

## 3) Train FastSpeech2

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\train.py -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

## 4) TensorBoard

```powershell
& 'C:\Users\anhhu\AppData\Roaming\Python\Python310\Scripts\tensorboard.exe' --logdir .\output\log\InfoRe1
```

## 5) Infer WAV chất lượng cao

Tải HiFi-GAN pretrained weights:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\download_hifigan_pretrained.py
```

Infer:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\synthesize.py --mode single --text "xin chao, day la fastspeech hai tieng viet" --restore_step 9000 -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

## 6) Ghi chú quan trọng

Clean repo này chủ yếu được chuẩn bị cho Kaggle và chia sẻ có thể tái lập.
Nếu GPU local yếu hơn Kaggle T4, bạn có thể cần giảm `batch_size` trong `config/InfoRe1_25hours/train.yaml`.

## 7) Lỗi thường gặp

- `UnicodeDecodeError`: đảm bảo file text là UTF-8.
- `TypeError: mel() takes 0 positional arguments`: repo này đã có fix tương thích librosa.
- thiếu vocoder checkpoint: chạy `python .\scripts\download_hifigan_pretrained.py`.
- MFA không tìm thấy: cài Montreal Forced Aligner trước và kiểm tra `mfa version`.
