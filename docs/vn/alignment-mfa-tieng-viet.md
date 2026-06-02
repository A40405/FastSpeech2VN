# Alignment MFA tiếng Việt

Tài liệu này mô tả đường alignment nghiêm túc hơn cho bản clean của repo FastSpeech2.

## Vì sao cần đường này

Đường bootstrap TextGrid trong repo chỉ nên dùng để smoke test nhanh. Nó chia đều thời lượng theo phone token, nên hữu ích để kiểm tra pipeline có chạy end-to-end hay không, nhưng không phải forced alignment thật.

Nếu bạn muốn duration target, phone boundary, nhịp đọc và vị trí ngắt nghỉ tốt hơn, hãy dùng Montreal Forced Aligner (MFA).

## Lựa chọn kỹ thuật của repo này

Repo này hiện dùng phone inventory tiếng Việt kiểu IPA trong `text/vietnamese.py`.
Vì vậy đường nghiêm túc hơn và nhất quán nhất là:

1. tạo từ điển phát âm IPA-style từ chính frontend tiếng Việt của repo
2. tạo MFA corpus từ raw files đã chuẩn bị
3. chạy `mfa train` để train MFA acoustic model và xuất TextGrid
4. chạy `preprocess.py` trên các TextGrid đó

Như vậy label của MFA sẽ khớp với đúng phone symbols kiểu IPA mà FastSpeech2 đang dùng trong repo.

## Repo này đang tận dụng ViMFA ở mức nào

Hiện tại repo học theo cách tổ chức của `ViMFA`: IPA-style lexicon, workflow `lexicon -> MFA -> TextGrid`, và tài liệu hóa rõ frontend tiếng Việt.

Tuy nhiên, repo này chưa bê nguyên các tài nguyên trọng tâm của `ViMFA` như G2P model đã train sẵn, acoustic model đã train sẵn, hay toàn bộ phone-set chuẩn hóa của repo đó.
Frontend trong repo vẫn là rule-based IPA frontend nội bộ, chưa phải một G2P model học máy riêng.

## Các script liên quan

- `scripts/build_infore1_mfa_assets.py`
- `scripts/run_mfa_train_alignment.py`
- `scripts/prepare_infore1_mfa.ps1`

## Cài MFA

Cách khuyến nghị:

```powershell
conda install -c conda-forge montreal-forced-aligner
```

Kiểm tra cài đặt:

```powershell
mfa version
```

## Quy trình từng bước

### 1) Chuẩn bị raw files

```powershell
python .\prepare_align.py .\config\InfoRe1_25hours\preprocess.yaml
```

### 2) Tạo MFA corpus và lexicon

```powershell
python .\scripts\build_infore1_mfa_assets.py --raw-root .\raw_data\InfoRe1 --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict
```

Output mong đợi:

- `mfa_corpus/InfoRe1/.../*.wav`
- `mfa_corpus/InfoRe1/.../*.lab`
- `mfa_assets/infore1_vi.dict`

### 3) Train MFA và xuất TextGrid

```powershell
python .\scripts\run_mfa_train_alignment.py --mfa mfa --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict --output-root .\preprocessed_data\InfoRe1\TextGrid --model-path .\mfa_assets\infore1_vi_acoustic_model.zip --num-jobs 4 --single-speaker --overwrite
```

Output mong đợi:

- `preprocessed_data/InfoRe1/TextGrid/.../*.TextGrid`
- `mfa_assets/infore1_vi_acoustic_model.zip`

### 4) Preprocess acoustic features

```powershell
python .\preprocess.py .\config\InfoRe1_25hours\preprocess.yaml
```

### 5) Train FastSpeech2

```powershell
python .\train.py -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

## Bản một lệnh

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1_mfa.ps1
```

## Khi nào nên dùng đường này

Dùng MFA khi:

- bạn cần phone boundary thực tế hơn
- bạn muốn duration supervision tốt hơn
- bạn muốn một bài train TTS tiếng Việt nghiêm túc hơn

Chỉ dùng bootstrap khi:

- bạn cần smoke test nhanh
- bạn đang debug preprocessing hoặc training setup
- bạn chưa muốn cài MFA

## Ghi chú quan trọng

Bản clean này không dùng trực tiếp official pretrained Vietnamese MFA acoustic model.
Thay vào đó, repo train MFA trên chính pronunciation inventory IPA-style của repo để label đầu ra vẫn tương thích với FastSpeech2 training.
