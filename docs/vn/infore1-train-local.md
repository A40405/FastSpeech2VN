# Hướng dẫn train local

Đây là workflow end-to-end chạy local cho repo clean.

## 1) Cài package

```powershell
$env:PYTHON_EXE = "python"
& $env:PYTHON_EXE -m pip install -r .\requirements-llama_gpu.txt
```

## 2) Chạy toàn bộ pipeline InfoRe1

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1 -PythonExe $env:PYTHON_EXE -MfaExe "mfa"
```

Script wrapper này đã chạy luôn:

- tải dataset
- chuẩn bị raw files
- sinh MFA assets
- train G2P model
- chạy MFA alignment
- validate alignment và phoneset
- preprocess FastSpeech2
- sinh `train.clean.txt` và `val.clean.txt`

Tài liệu chi tiết:

- `mfa-tieng-viet-can-chinh.md`

## 3) Train FastSpeech2

```powershell
& $env:PYTHON_EXE .\train.py -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

Preset `config/InfoRe1_25hours/train.yaml` hiện đã được siết theo hướng retrain an toàn hơn:

- `batch_size: 4`
- `grad_acc_step: 4`
- `group_size: 2`
- `num_workers: 2`
- `AMP` tắt mặc định để dễ chẩn đoán

## 3.1) Tạo clean subset trước khi retrain

Sau khi đã có `alignment_validation_report.json`, tạo lại split sạch hơn:

```powershell
& $env:PYTHON_EXE .\scripts\build_infore1_clean_subset.py --config .\config\InfoRe1_25hours\preprocess.yaml
```

Lệnh này sinh:

- `preprocessed_data/InfoRe1/train.clean.txt`
- `preprocessed_data/InfoRe1/val.clean.txt`
- `preprocessed_data/InfoRe1/clean_subset_report.json`

Bộ clean subset hiện tại được siết chặt hơn cho TTS tiếng Việt câu dài:

- `min_total_duration_frames: 48`
- `max_zero_duration_repaired: 0`
- `max_one_frame_non_silence_count: 10`
- `max_one_frame_non_silence_ratio: 0.10`
- `max_pause_frame_ratio: 0.25`
- `max_token_count: 110`

Ngưỡng này sẽ loại bớt các mẫu dài hoặc nhiễu, vốn thường nghe ổn ở đầu câu nhưng càng về sau càng dễ vỡ.

Muốn train trên clean subset, đổi trong `config/InfoRe1_25hours/train.yaml`:

```yaml
dataset:
  train_file: "train.clean.txt"
  val_file: "val.clean.txt"
```

## 4) TensorBoard

```powershell
& $env:PYTHON_EXE -m tensorboard.main --logdir .\output\log\InfoRe1
```

## 5) Infer WAV chất lượng cao

Tải HiFi-GAN pretrained weights:

```powershell
& $env:PYTHON_EXE .\scripts\download_hifigan_pretrained.py
```

Infer:

```powershell
& $env:PYTHON_EXE .\synthesize.py --mode single --text "xin chao, day la fastspeech hai tieng viet" --restore_step 9000 -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

## 6) Ghi chú quan trọng

Clean repo này chủ yếu được chuẩn bị cho Kaggle và chia sẻ có thể tái lập.
Nếu GPU local yếu hơn Kaggle T4, bạn vẫn có thể giảm thêm `batch_size`, nhưng preset hiện tại đã ưu tiên ổn định hơn tốc độ.
Sau bước preprocess, bạn nên xem thêm:

- `preprocessed_data/InfoRe1/alignment_validation_report.json`
- `preprocessed_data/InfoRe1/clean_subset_report.json`
- `mfa_assets/phoneset_report.json`

## 6.1) Đánh giá sớm các checkpoint 8000 / 16000 / 24000

Để nghe nhanh 3 câu kiểm tra ngắn:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\evaluate_infore1_checkpoints.ps1 -PythonExe $env:PYTHON_EXE
```

Script này synthesize các câu:

- `xin chào bạn`
- `mời bạn ngồi xuống`
- `hôm nay trời đẹp`

và lưu kết quả vào `output/result/InfoRe1_eval/step_8000`, `step_16000`, `step_24000`.

## 7) Lỗi thường gặp

- `UnicodeDecodeError`: đảm bảo file text là UTF-8.
- `TypeError: mel() takes 0 positional arguments`: repo này đã có fix tương thích librosa.
- thiếu vocoder checkpoint: chạy `python .\scripts\download_hifigan_pretrained.py`.
- MFA không tìm thấy: cài Montreal Forced Aligner trước và kiểm tra `mfa version`.
