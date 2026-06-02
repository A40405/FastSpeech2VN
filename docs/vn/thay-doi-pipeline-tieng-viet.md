# Thay đổi pipeline tiếng Việt

Tài liệu này tóm tắt các thay đổi chính được thêm vào trên nền repo gốc `ming024/FastSpeech2`.

## Mục tiêu chính

Giữ nguyên kiến trúc FastSpeech2, nhưng điều chỉnh dữ liệu, text frontend và workflow để train tiếng Việt với `doof-ferb/infore1_25hours`.

## Các thay đổi lớn

### Frontend tiếng Việt

- thêm `text/vietnamese.py`
- thay phone inventory cũ dạng `on_ / v_ / cod_ / tone_` bằng phone inventory tiếng Việt kiểu IPA
- giữ `phonemize_text()` dạng rule-based để xử lý transcript tiếng Việt, nhưng đầu ra bây giờ là IPA-style và hướng theo cách tổ chức lexicon của `ViMFA`

### Mức độ tận dụng ViMFA

- repo hiện tại học theo hướng tổ chức của `ViMFA`: IPA-style lexicon, workflow `lexicon -> MFA -> TextGrid`, và tài liệu hóa rõ frontend tiếng Việt
- repo chưa bê nguyên các tài nguyên trọng tâm của `ViMFA` như G2P model đã train, acoustic model đã train, hay toàn bộ phone-set chuẩn hóa của repo đó
- vì vậy bản hiện tại nên được hiểu là `ViMFA-inspired IPA pipeline`, chưa phải là một bản tích hợp đầy đủ `ViMFA`

### Quy trình tải dataset

- viết lại `scripts/download_infore1_dataset.py`
- dataset được tải trực tiếp vào workspace của dự án thay vì phụ thuộc `.cache/huggingface`
- file giải nén được đặt trong `corpus/infore1_25hours/`

### Chuẩn bị raw-data cho InfoRe1

- thêm `preprocessor/infore1.py`
- cập nhật `prepare_align.py` để hỗ trợ `InfoRe1`
- bước raw preparation sẽ tạo `.wav`, `.lab` và `.phones`

### Đường bootstrap alignment

- cập nhật `scripts/bootstrap_textgrids.py`
- TextGrid bootstrap được tạo từ `.phones`
- đường này chỉ nên dùng cho smoke test hoặc dựng pipeline nhanh

### Đường MFA nghiêm túc hơn

- thêm `scripts/build_infore1_mfa_assets.py`
- thêm `scripts/run_mfa_train_alignment.py`
- thêm `scripts/prepare_infore1_mfa.ps1`
- đường này bây giờ train MFA trên phone inventory IPA-style của repo rồi xuất TextGrid thật

### Sửa tương thích runtime

- cập nhật các phần audio, preprocessing và vocoder loading để hợp với stack Python/librosa/runtime hiện tại
- cải thiện xử lý lỗi khi thiếu vocoder checkpoint

### Quản lý HiFi-GAN

- thêm `scripts/download_hifigan_pretrained.py`
- cập nhật cách load vocoder để báo lỗi rõ ràng hơn khi thiếu checkpoint

### Workflow cho Kaggle

- thêm `kaggle_fastspeech2vn.ipynb`
- thêm `kaggle_fastspeech2vn_mfa.ipynb`
- thêm `requirements-kaggle.txt`
- bản clean được chuẩn bị theo hướng dễ đưa lên GitHub và chạy trên Kaggle

### Lớp dịch vụ từ xa tùy chọn

- thêm `api/train_infer_api.py`
- thêm `api/embed_api.py`
- thêm `scripts/start_ngrok_services.py`

## Ghi chú quan trọng

Repo clean và repo local đang chạy dữ liệu thật không phải là một.
Bản clean là bản gọn hơn, dùng để chia sẻ lên GitHub và chạy lại trên Kaggle.
