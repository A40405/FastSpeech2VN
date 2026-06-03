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
- `preprocessed_data/InfoRe1/TextGrid`

## Vì sao vẫn chưa phải bản sao đầy đủ của ViMFA

Repo này đã đi theo đúng cấu trúc thực dụng của ViMFA:

- lexicon tiếng Việt kiểu IPA
- dữ liệu train G2P
- tài nguyên alignment cho MFA
- word list và symbol mapping rõ ràng

Tuy nhiên, repo này vẫn chưa bê nguyên các tài nguyên lõi của ViMFA:

- frontend vẫn là rule-based và chạy nội bộ trong repo
- G2P model được train từ dữ liệu IPA đã xuất ra, chứ không phải lấy thẳng từ ViMFA
- acoustic alignment model cũng được train trong workflow của repo, chứ không phải bundle sẵn từ ViMFA

Vì vậy, dự án nên được hiểu là `ViMFA-inspired` và gần hơn với một stack TTS tiếng Việt thực tế, nhưng vẫn là một bản tự chứa.

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
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1
```

Script wrapper này sẽ gọi luôn toàn bộ pipeline MFA, bao gồm bước train G2P.

Nếu muốn chạy tay từng bước alignment, hai lệnh chính là:

```powershell
python .\scripts\train_vietnamese_g2p.py --mfa mfa --dictionary-path .\mfa_assets\infore1_vi_g2p.tsv --output-model-path .\mfa_assets\infore1_vi_g2p_model.zip --overwrite
```

```powershell
python .\scripts\run_mfa_train_alignment.py --mfa mfa --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict --output-root .\preprocessed_data\InfoRe1\TextGrid --model-path .\mfa_assets\infore1_vi_acoustic_model.zip --num-jobs 4 --single-speaker --overwrite
```

## Ghi chú chất lượng

- Alignment tốt hơn thường tạo duration target tốt hơn cho FastSpeech2.
- Nếu `TextGrid` đã tồn tại, bạn có thể bỏ qua bước MFA.
- Repo clean được thiết kế để chia sẻ công khai và tái lập dễ hơn.
