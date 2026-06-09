# Docs Index

Project-specific documentation for the Vietnamese InfoRe1 pipeline is organized here.

Reference platform notebooks also live in:

- `../notebooks/kaggle_fastspeech2vn_train.ipynb`
- `../notebooks/colab_fastspeech2vn_mfa.ipynb`

## English

- `en/infore1-setup.md`: overview of the customized InfoRe1 setup
- `en/infore1-local-train-guide.md`: step-by-step local workflow from data download to training and inference
- `en/mfa-vietnamese-alignment.md`: serious Vietnamese alignment path using Montreal Forced Aligner
- `en/infore1-local-train-guide.md`: also documents the safer retrain preset and `train.clean.txt` / `val.clean.txt` flow
- `en/ngrok-services.md`: notes for remote API and ngrok tunnels
- `en/infore1-vietnamese-demo.md`: how to generate the Vietnamese demo package
- `en/vietnamese-pipeline-changes.md`: summary of code changes made on top of upstream FastSpeech2

## Vietnamese

- `vn/infore1-cai-dat.md`: tổng quan cài đặt cho InfoRe1
- `vn/infore1-train-local.md`: quy trình train local từng bước
- `vn/infore1-train-local.md`: đồng thời ghi rõ preset retrain an toàn hơn và cách sinh `train.clean.txt` / `val.clean.txt`
- `vn/mfa-tieng-viet-can-chinh.md`: hướng alignment nghiêm túc hơn bằng MFA
- `vn/dich-vu-ngrok.md`: ghi chú về API và ngrok
- `vn/infore1-demo-tieng-viet.md`: cách tạo demo tiếng Việt tự động
- `vn/thay-doi-pipeline-tieng-viet.md`: tóm tắt các thay đổi code cho pipeline tiếng Việt
