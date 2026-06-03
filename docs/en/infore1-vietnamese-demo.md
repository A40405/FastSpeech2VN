# Vietnamese Demo

This repo now treats the demo area as a Vietnamese-only export folder for InfoRe1.

## Goal

The demo is meant to show Vietnamese ground-truth audio and synthesized audio from the current pipeline.

## Folder layout

The generated structure looks like this:

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

## How to generate it

Run the demo builder after you have synthesized outputs:

```powershell
python .\scripts\build_infore1_demo.py
```

By default, the script looks for:

- raw Vietnamese audio in `raw_data/InfoRe1`
- synthesized WAV files in `output/result/InfoRe1`

If you want to stage files manually first, you can put them in a folder such as:

```text
demo/InfoRe1/inbox/
```

and run:

```powershell
python .\scripts\build_infore1_demo.py --pair-root .\demo\InfoRe1\inbox
```

## What to place there later

For each sample, provide:

- a ground-truth WAV
- a synthesized WAV
- an optional transcript text file

The script will copy and package them into `demo/InfoRe1/samples/` automatically.
