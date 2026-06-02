# Thay doi pipeline tieng Viet

Tai lieu nay tom tat cac thay doi chinh duoc them vao tren nen repo goc `ming024/FastSpeech2`.

## Muc tieu chinh

Giu nguyen kien truc FastSpeech2, nhung dieu chinh du lieu, text frontend va workflow de train tieng Viet voi `doof-ferb/infore1_25hours`.

## Cac thay doi lon

### Frontend tieng Viet

- them `text/vietnamese.py`
- thay phone inventory cu dang `on_ / v_ / cod_ / tone_` bang phone inventory tieng Viet kieu IPA
- giu `phonemize_text()` dang rule-based de xu ly transcript tieng Viet, nhung dau ra bay gio la IPA-style va huong theo cach to chuc lexicon cua ViMFA

### Quy trinh tai dataset

- viet lai `scripts/download_infore1_dataset.py`
- dataset duoc tai truc tiep vao workspace cua du an thay vi phu thuoc `.cache/huggingface`
- file giai nen duoc dat trong `corpus/infore1_25hours/`

### Chuan bi raw-data cho InfoRe1

- them `preprocessor/infore1.py`
- cap nhat `prepare_align.py` de ho tro `InfoRe1`
- buoc raw preparation se tao `.wav`, `.lab` va `.phones`

### Duong bootstrap alignment

- cap nhat `scripts/bootstrap_textgrids.py`
- TextGrid bootstrap duoc tao tu `.phones`
- duong nay chi nen dung cho smoke test hoac dung pipeline nhanh

### Duong MFA nghiem tuc hon

- them `scripts/build_infore1_mfa_assets.py`
- them `scripts/run_mfa_train_alignment.py`
- them `scripts/prepare_infore1_mfa.ps1`
- duong nay bay gio train MFA tren phone inventory IPA-style cua repo roi xuat TextGrid that

### Sua tuong thich runtime

- cap nhat cac phan audio, preprocessing va vocoder loading de hop voi stack Python/librosa/runtime hien tai
- cai thien xu ly loi khi thieu vocoder checkpoint

### Quan ly HiFi-GAN

- them `scripts/download_hifigan_pretrained.py`
- cap nhat cach load vocoder de bao loi ro rang hon khi thieu checkpoint

### Workflow cho Kaggle

- them `kaggle_fastspeech2vn.ipynb`
- them `requirements-kaggle.txt`
- ban clean duoc chuan bi theo huong de dua len GitHub va chay tren Kaggle

### Lop dich vu tu xa tuy chon

- them `api/train_infer_api.py`
- them `api/embed_api.py`
- them `scripts/start_ngrok_services.py`

## Ghi chu quan trong

Repo clean va repo local dang chay du lieu that khong phai la mot.
Ban clean la ban gon hon, dung de chia se len GitHub va chay lai tren Kaggle.
