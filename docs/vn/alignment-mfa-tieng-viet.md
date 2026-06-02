# Alignment MFA tieng Viet

Tai lieu nay mo ta duong alignment nghiem tuc hon cho ban clean cua repo FastSpeech2.

## Vi sao can duong nay

Duong bootstrap TextGrid trong repo chi nen dung de smoke test nhanh. No chia deu thoi luong theo phone token, nen huu ich de kiem tra pipeline co chay end-to-end hay khong, nhung khong phai forced alignment that.

Neu ban muon duration target, phone boundary, nhip doc va vi tri ngat nghi tot hon, hay dung Montreal Forced Aligner (MFA).

## Lua chon ky thuat cua repo nay

Repo nay hien dung phone inventory tieng Viet kieu IPA trong `text/vietnamese.py`.
Vi vay duong nghiem tuc hon va nhat quan nhat la:

1. tao tu dien phat am IPA-style tu chinh frontend tieng Viet cua repo
2. tao MFA corpus tu raw files da chuan bi
3. chay `mfa train` de train MFA acoustic model va xuat TextGrid
4. chay `preprocess.py` tren cac TextGrid do

Nhu vay label cua MFA se khop voi dung phone symbols kieu IPA ma FastSpeech2 dang dung trong repo.

## Vi tri cua repo nay so voi ViMFA

Huong nay giong pipeline thuc te hon so voi phone set cu, vi repo bay gio tao lexicon va MFA labels kieu ViMFA tu cung mot frontend IPA-style.
Tuy nhien frontend trong repo van la dang rule-based, chua phai mot G2P model hoc may rieng.

## Cac script moi

- `scripts/build_infore1_mfa_assets.py`
- `scripts/run_mfa_train_alignment.py`
- `scripts/prepare_infore1_mfa.ps1`

## Cai MFA

Cach khuyen nghi:

```powershell
conda install -c conda-forge montreal-forced-aligner
```

Kiem tra cai dat:

```powershell
mfa version
```

## Quy trinh tung buoc

### 1) Chuan bi raw files

```powershell
python .\prepare_align.py .\config\InfoRe1_25hours\preprocess.yaml
```

### 2) Tao MFA corpus va lexicon

```powershell
python .\scripts\build_infore1_mfa_assets.py --raw-root .\raw_data\InfoRe1 --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict
```

Output mong doi:

- `mfa_corpus/InfoRe1/.../*.wav`
- `mfa_corpus/InfoRe1/.../*.lab`
- `mfa_assets/infore1_vi.dict`

### 3) Train MFA va xuat TextGrid

```powershell
python .\scripts\run_mfa_train_alignment.py --mfa mfa --corpus-root .\mfa_corpus\InfoRe1 --lexicon-path .\mfa_assets\infore1_vi.dict --output-root .\preprocessed_data\InfoRe1\TextGrid --model-path .\mfa_assets\infore1_vi_acoustic_model.zip --num-jobs 4 --single-speaker --overwrite
```

Output mong doi:

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

## Ban mot lenh

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1_mfa.ps1
```

## Khi nao nen dung duong nay

Dung MFA khi:

- ban can phone boundary thuc te hon
- ban muon duration supervision tot hon
- ban muon mot bai train TTS tieng Viet nghiem tuc hon

Chi dung bootstrap khi:

- ban can smoke test nhanh
- ban dang debug preprocessing hoac training setup
- ban chua muon cai MFA

## Ghi chu quan trong

Ban clean nay khong dung truc tiep official pretrained Vietnamese MFA acoustic model.
Thay vao do, repo train MFA tren chinh pronunciation inventory IPA-style cua repo de label dau ra van tuong thich voi FastSpeech2 training.
