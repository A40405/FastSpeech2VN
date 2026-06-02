# Hướng dẫn train local

Đây là quy trình local end-to-end cho bản clean của repo.

## 1) Cài package

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' -m pip install -r .\requirements-llama_gpu.txt
```

## 2) Tải dataset

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\download_infore1_dataset.py --dataset doof-ferb/infore1_25hours --split train --output-dir .\corpus\infore1_25hours
```

Output mong đợi:

- `corpus/infore1_25hours/metadata.csv`
- `corpus/infore1_25hours/wavs/*.wav`
- `corpus/infore1_25hours/_downloads/train/*.parquet`

## 3) Chuẩn bị raw files

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\prepare_align.py .\config\InfoRe1_25hours\preprocess.yaml
```

Output mong đợi:

- `raw_data/InfoRe1/InfoRe1/*.wav`
- `raw_data/InfoRe1/InfoRe1/*.lab`
- `raw_data/InfoRe1/InfoRe1/*.phones`

## 4) Chọn đường alignment

### Cách A: bootstrap nhanh

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\bootstrap_textgrids.py --raw-root .\raw_data\InfoRe1 --output-root .\preprocessed_data\InfoRe1\TextGrid
```

### Cách B: MFA nghiêm túc hơn

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1_mfa.ps1
```

Nếu bạn dùng đường MFA thì script này đã chạy luôn download, prepare-align, tạo MFA assets, train/alignment export bằng MFA, và `preprocess.py`.

Tài liệu chi tiết:

- `alignment-mfa-tieng-viet.md`

## 5) Preprocess acoustic features

Chỉ chạy bước này nếu bạn dùng đường bootstrap:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\preprocess.py .\config\InfoRe1_25hours\preprocess.yaml
```

## 6) Train FastSpeech2

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\train.py -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

## 7) TensorBoard

```powershell
& 'C:\Users\anhhu\AppData\Roaming\Python\Python310\Scripts\tensorboard.exe' --logdir .\output\log\InfoRe1
```

## 8) Infer WAV chất lượng cao

Tải HiFi-GAN pretrained weights:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\scripts\download_hifigan_pretrained.py
```

Infer:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\synthesize.py --mode single --text "xin chao, day la fastspeech hai tieng viet" --restore_step 9000 -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

## 9) Lưu ý quan trọng cho bản clean này

Bản clean chủ yếu được chuẩn bị để chia sẻ và chạy trên Kaggle.
Nếu GPU local của bạn yếu hơn Kaggle T4, bạn có thể cần giảm `batch_size` trong `config/InfoRe1_25hours/train.yaml`.

## 10) Lỗi thường gặp

- `UnicodeDecodeError`: cần đảm bảo file text là UTF-8.
- `TypeError: mel() takes 0 positional arguments`: repo này đã có fix tương thích librosa.
- thiếu vocoder checkpoint: chạy `python .\scripts\download_hifigan_pretrained.py`.
- không tìm thấy MFA: cài Montreal Forced Aligner trước và kiểm tra `mfa version`.
