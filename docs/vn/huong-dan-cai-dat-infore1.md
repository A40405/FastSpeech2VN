# Hướng dẫn cài đặt InfoRe1

Repo này giữ nguyên kiến trúc FastSpeech2 và bổ sung pipeline tiếng Việt cho dataset Hugging Face `doof-ferb/infore1_25hours`.

## Repo này dùng để làm gì

- tải InfoRe1 trực tiếp về workspace 
- chuyển transcript tiếng Việt sang phone inventory kiểu IPA trong `text/vietnamese.py`
- chuẩn bị dữ liệu thô cho train
- xuất thêm các tài nguyên kiểu ViMFA cho MFA và G2P:
  - `mfa_assets/infore1_vi.dict`
  - `mfa_assets/infore1_vi_g2p.tsv`
  - `mfa_assets/infore1_vi.wordlist`
  - `mfa_assets/infore1_vi_symbol_map.tsv`
- hỗ trợ hai đường alignment:
  - đường bootstrap TextGrid nhanh để smoke test
  - đường MFA nghiêm túc hơn để có duration và phone boundary tốt hơn
- train và infer bằng FastSpeech2

## Môi trường chính

### Kaggle

Dùng `requirements-kaggle.txt`.
Notebook Kaggle nên để ngoài repo Git, trong workspace riêng của bạn.

### Máy local

Dùng:

- `requirements-llama_gpu.txt`
- `scripts/prepare_infore1.ps1` cho đường bootstrap nhanh
- `scripts/prepare_infore1_mfa.ps1` cho đường MFA nghiêm túc hơn

## Ghi chú về frontend IPA

Repo này đã bỏ phone set cũ dạng `on_ / v_ / cod_ / tone_`.
Hiện tại `.phones`, lexicon của MFA, dữ liệu train G2P và text symbols của FastSpeech2 đều dùng cùng một bộ nhãn IPA-style cho tiếng Việt.

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

Nếu bạn muốn train thêm một MFA G2P model từ dữ liệu IPA tiếng Việt đã xuất ra, chạy tiếp:

```powershell
python .\scripts\train_vietnamese_g2p.py --mfa mfa --dictionary-path .\mfa_assets\infore1_vi_g2p.tsv --output-model-path .\mfa_assets\infore1_vi_g2p_model.zip --overwrite
```

Tài liệu chi tiết:

- `alignment-mfa-tieng-viet.md`

## Ghi chú

- Bản clean hiện chỉ có `config/InfoRe1_25hours/train.yaml`.
- Trong repo clean này, `train.yaml` là cấu hình train đang được notebook Kaggle sử dụng.
- Nếu chạy trên GPU local yếu hơn, bạn có thể cần giảm `batch_size` hoặc tăng `grad_acc_step`.
