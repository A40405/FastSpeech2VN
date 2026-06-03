# Hướng dẫn cài đặt InfoRe1

Repository này giữ nguyên kiến trúc FastSpeech2 và thêm pipeline tiếng Việt cho bộ dữ liệu Hugging Face `doof-ferb/infore1_25hours`.

## Mục đích của repo

- tải InfoRe1 trực tiếp về workspace thay vì phụ thuộc `.cache/huggingface`
- chuyển transcript tiếng Việt sang phone inventory kiểu IPA được định nghĩa trong `text/vietnamese.py`
- chuẩn bị file thô để train
- xuất các tài nguyên theo kiểu ViMFA cho MFA và G2P:
  - `mfa_assets/infore1_vi.dict`
  - `mfa_assets/infore1_vi_g2p.tsv`
  - `mfa_assets/infore1_vi.wordlist`
  - `mfa_assets/infore1_vi_symbol_map.tsv`
- train một G2P model MFA có thể tái sử dụng từ lexicon IPA đã xuất
- chạy alignment bằng MFA và preprocess FastSpeech2 trong một flow đầy đủ
- train và infer với FastSpeech2

## Môi trường chính

### Kaggle

Dùng `requirements-kaggle.txt`.
Notebook Kaggle phải để ngoài repo Git, trong workspace riêng của bạn.

### Máy local

Dùng:

- `requirements-llama_gpu.txt`
- `scripts/prepare_infore1.ps1` hoặc `scripts/prepare_infore1_mfa.ps1` cho flow đầy đủ

## Ghi chú về frontend IPA

Repo hiện dùng phone inventory tiếng Việt kiểu IPA thay cho bộ nhãn cũ `on_ / v_ / cod_ / tone_`.
Điều đó có nghĩa là file `.phones`, lexicon MFA, dữ liệu train G2P và symbol FastSpeech2 đều dùng cùng một hệ nhãn IPA tiếng Việt.

Repo này vẫn chưa phải bản sao y hệt `ViMFA`, nhưng đã có đủ các khối thực dụng quan trọng: dữ liệu từ điển phát âm, dữ liệu train G2P, word list và symbol mapping.

## Pipeline local đầy đủ

Cài package:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' -m pip install -r .\requirements-llama_gpu.txt
```

Chạy toàn bộ pipeline InfoRe1:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1
```

Script wrapper này sẽ gọi luôn pipeline MFA đầy đủ, bao gồm cả bước train G2P.

## Nhánh MFA nghiêm túc

Nếu bạn muốn chạy riêng từng bước, dùng:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1_mfa.ps1
```

Nếu muốn train riêng G2P model MFA từ dữ liệu lexicon IPA tiếng Việt đã xuất ra, chạy tiếp:

```powershell
python .\scripts\train_vietnamese_g2p.py --mfa mfa --dictionary-path .\mfa_assets\infore1_vi_g2p.tsv --output-model-path .\mfa_assets\infore1_vi_g2p_model.zip --overwrite
```

Tài liệu chi tiết:

- `mfa-vietnamese-alignment.md`

## Ghi chú

- Clean repo hiện chỉ giữ `config/InfoRe1_25hours/train.yaml`.
- Trong clean repo này, `train.yaml` là cấu hình train đang được notebook Kaggle sử dụng.
- Nếu chạy trên GPU local yếu hơn Kaggle T4, có thể phải giảm `batch_size` hoặc tăng `grad_acc_step`.
