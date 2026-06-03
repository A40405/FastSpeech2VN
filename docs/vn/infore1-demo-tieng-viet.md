# Demo tiếng Việt

Repo này bây giờ coi khu vực demo là thư mục xuất mẫu riêng cho InfoRe1 tiếng Việt.

## Mục tiêu

Demo dùng để trình bày audio tiếng Việt gốc và audio sinh ra từ pipeline hiện tại.
Nó không tái sử dụng bộ showcase tiếng Anh/Trung của upstream nữa.

## Cấu trúc thư mục

Cấu trúc được tạo ra sẽ giống như sau:

```text
demo/InfoRe1/
  README.md
  index.md
  manifest.json
  samples/
    <sample_id>/
      ground-truth.wav
      synthesized.wav
      transcript.txt
```

## Cách tạo tự động

Sau khi bạn đã có file synthesized, chạy script build demo:

```powershell
python .\scripts\build_infore1_demo.py
```

Mặc định script sẽ tìm:

- audio gốc tiếng Việt trong `raw_data/InfoRe1`
- file WAV sinh ra trong `output/result/InfoRe1`

Nếu muốn tự stage file trước, bạn có thể thả chúng vào thư mục kiểu:

```text
demo/InfoRe1/inbox/
```

rồi chạy:

```powershell
python .\scripts\build_infore1_demo.py --pair-root .\demo\InfoRe1\inbox
```

## Sau này chỉ cần thả gì vào đây

Mỗi sample cần tối thiểu:

- một file WAV ground-truth
- một file WAV synthesized
- một file transcript text nếu có

Script sẽ tự copy và đóng gói vào `demo/InfoRe1/samples/`.
