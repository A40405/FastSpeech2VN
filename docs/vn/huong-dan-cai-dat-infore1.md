# Huong dan cai dat InfoRe1

Repo nay giu nguyen kien truc FastSpeech2 va bo sung pipeline tieng Viet cho dataset Hugging Face `doof-ferb/infore1_25hours`.

## Repo nay dung de lam gi

- tai InfoRe1 truc tiep ve workspace thay vi phu thuoc `.cache/huggingface`
- chuyen transcript tieng Viet sang phone inventory kieu IPA trong `text/vietnamese.py`
- chuan bi du lieu tho cho train
- ho tro hai duong alignment:
  - duong bootstrap TextGrid nhanh de smoke test
  - duong MFA nghiem tuc hon de co duration va phone boundary tot hon
- train va infer bang FastSpeech2

## Moi truong chinh

### Kaggle

Dung:

- `kaggle_fastspeech2vn.ipynb`
- `requirements-kaggle.txt`

Day la duong khuyen nghi neu ban muon train bang GPU voi ban clean.

### May local

Dung:

- `requirements-llama_gpu.txt`
- `scripts/prepare_infore1.ps1` cho duong bootstrap nhanh
- `scripts/prepare_infore1_mfa.ps1` cho duong MFA nghiem tuc hon

## Ghi chu ve frontend IPA

Repo nay da bo phone set cu dang `on_ / v_ / cod_ / tone_`.
Hien tai `.phones`, lexicon cua MFA va text symbols cua FastSpeech2 deu dung cung mot bo nhan IPA-style cho tieng Viet.

## Duong bootstrap nhanh

Cai package:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' -m pip install -r .\requirements-llama_gpu.txt
```

Chuan bi du lieu:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1.ps1
```

Train:

```powershell
& 'D:\Anaconda\envs\llama_gpu\python.exe' .\train.py -p .\config\InfoRe1_25hours\preprocess.yaml -m .\config\InfoRe1_25hours\model.yaml -t .\config\InfoRe1_25hours\train.yaml
```

## Duong MFA nghiem tuc hon

Neu ban muon phone boundary va duration target tot hon, dung:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare_infore1_mfa.ps1
```

Tai lieu chi tiet:

- `alignment-mfa-tieng-viet.md`

## Ghi chu

- Ban clean hien chi co `config/InfoRe1_25hours/train.yaml`.
- Trong repo clean nay, `train.yaml` la cau hinh train dang duoc notebook Kaggle su dung.
- Neu chay tren GPU local yeu hon, ban co the can giam `batch_size` hoac tang `grad_acc_step`.
