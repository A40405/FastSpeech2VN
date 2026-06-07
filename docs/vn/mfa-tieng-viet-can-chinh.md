# Alignment MFA tiếng Việt

Tài liệu này mô tả đường alignment tiếng Việt đầy đủ trong repo clean.

## Ý tưởng chính

Repo hiện giữ frontend tiếng Việt kiểu IPA và dùng MFA để alignment.
Đường được khuyến nghị là pipeline đầy đủ, không phải đường bootstrap xấp xỉ.

## Pipeline tạo ra gì

- `mfa_assets/infore1_vi.dict`
- `mfa_assets/infore1_vi_g2p.tsv`
- `mfa_assets/infore1_vi.wordlist`
- `mfa_assets/infore1_vi_symbol_map.tsv`
- `mfa_assets/infore1_vi_g2p_model.zip`
- `mfa_assets/phoneset_report.json`
- `preprocessed_data/InfoRe1/TextGrid`
- `preprocessed_data/InfoRe1/alignment_validation_report.json`

## Vì sao vẫn chưa phải bản sao đầy đủ của ViMFA

Repo này đã đi theo đúng cấu trúc thực dụng của ViMFA:

- lexicon tiếng Việt kiểu IPA
- dữ liệu train G2P
- tài nguyên alignment cho MFA
- word list và symbol mapping rõ ràng


## Luồng alignment đầy đủ

1. tải dataset
2. chuẩn bị file audio/text thô
3. xuất MFA assets và bộ train G2P
4. train MFA G2P model
5. train MFA acoustic aligner
6. xuất `TextGrid`
7. preprocess đặc trưng FastSpeech2
8. train FastSpeech2

## Chạy local bằng một lệnh

Dùng wrapper pipeline đầy đủ:

```powershell
$env:PYTHON_EXE = "python"
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1 -PythonExe $env:PYTHON_EXE -MfaExe "mfa"
```

Wrapper này gọi sang `scripts/prepare_infore1_mfa.ps1`, và script đó chạy trọn pipeline MFA gồm cả train G2P.

Nếu muốn chạy tay từng bước alignment, hai lệnh chính là:

```powershell
python .\scripts\build_infore1_mfa_assets.py --raw-root .\raw_data\InfoRe1 --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict --g2p-train-path .\mfa_assets\infore1_vi_g2p.tsv --wordlist-path .\mfa_assets\infore1_vi.wordlist --symbol-map-path .\mfa_assets\infore1_vi_symbol_map.tsv
```

```powershell
python .\scripts\train_vietnamese_g2p.py --mfa mfa --dictionary-path .\mfa_assets\infore1_vi.dict --output-model-path .\mfa_assets\infore1_vi_g2p_model.zip --overwrite
```

```powershell
python .\scripts\run_mfa_train_alignment.py --mfa mfa --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict --output-root .\preprocessed_data\InfoRe1\TextGrid --model-path .\mfa_assets\infore1_vi_acoustic_model.zip --num-jobs 4 --single-speaker --overwrite
```

Trước khi preprocess, nên chạy thêm:

```powershell
python .\scripts\validate_alignment.py --config .\config\InfoRe1_25hours\preprocess.yaml
python .\scripts\check_phoneset.py --config .\config\InfoRe1_25hours\preprocess.yaml
```

Hai report quan trọng cần xem là:

- `preprocessed_data/InfoRe1/alignment_validation_report.json`
- `mfa_assets/phoneset_report.json`

## Ghi chú chất lượng

- Alignment tốt hơn thường tạo duration target tốt hơn cho FastSpeech2.
- Repo hiện có bước repair `zero-duration` trong preprocess, nhưng không nuốt lỗi âm thầm: lỗi và số lượng sửa đều được thống kê trong report.
- Khi rebuild `dict` và `g2p.tsv`, repo sẽ tự thêm một nhóm nhỏ coverage seed cho các IPA symbol hiếm chỉ có trong frontend để phoneset đồng bộ hơn.
- Nếu `TextGrid` đã tồn tại, bạn có thể bỏ qua bước MFA.
- Repo clean được thiết kế để chia sẻ công khai và tái lập dễ hơn.
