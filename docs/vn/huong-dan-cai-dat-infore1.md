# Hướng dẫn cài đặt InfoRe1

Repo này giữ nguyên kiến trúc FastSpeech2 và bổ sung pipeline tiếng Việt cho dataset Hugging Face `doof-ferb/infore1_25hours`.

## Repo này dùng để làm gì

- tải InfoRe1 trực tiếp về workspace thay vì phụ thuộc `.cache/huggingface`
- chuyển transcript tiếng Việt sang phone inventory kiểu IPA trong `text/vietnamese.py`
- chuẩn bị dữ liệu thô cho train
- hỗ trợ hai đường alignment:
  - đường bootstrap TextGrid nhanh để smoke test
  - đường MFA nghiêm túc hơn để có duration và phone boundary tốt hơn
- train và infer bằng FastSpeech2

## Môi trường chính

### Kaggle

Dùng:

- `kaggle_fastspeech2vn.ipynb`
- `kaggle_fastspeech2vn_mfa.ipynb`
- `requirements-kaggle.txt`

Đây là đường khuyến nghị nếu bạn muốn train bằng GPU với bản clean.

### Máy local

Dùng:

- `requirements-llama_gpu.txt`
- `scripts/prepare_infore1.ps1` cho đường bootstrap nhanh
- `scripts/prepare_infore1_mfa.ps1` cho đường MFA nghiêm túc hơn

## Ghi chú về frontend IPA

Repo này đã bỏ phone set cũ dạng `on_ / v_ / cod_ / tone_`.
Hiện tại `.phones`, lexicon của MFA và text symbols của FastSpeech2 đều dùng cùng một bộ nhãn IPA-style cho tiếng Việt.

Pipeline này học theo hướng tổ chức của `ViMFA`, nhưng chưa bê nguyên toàn bộ tài nguyên của repo đó vào đây.
Cụ thể, frontend hiện tại vẫn là rule-based IPA frontend nội bộ của repo, chưa phải một G2P model được train riêng như trong `ViMFA`.

## Đường bootstrap nhanh

Cài package:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' -m pip install -r .\requirements-llama_gpu.txt
```

Chuẩn bị dữ liệu:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1
```

Train:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\train.py -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

## Đường MFA nghiêm túc hơn

Nếu bạn muốn phone boundary và duration target tốt hơn, dùng:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1_mfa.ps1
```

Tài liệu chi tiết:

- `alignment-mfa-tieng-viet.md`

## Ghi chú

- Bản clean hiện chỉ có `config/InfoRe1_25hours/train.yaml`.
- Trong repo clean này, `train.yaml` là cấu hình train đang được notebook Kaggle sử dụng.
- Nếu chạy trên GPU local yếu hơn, bạn có thể cần giảm `batch_size` hoặc tăng `grad_acc_step`.
