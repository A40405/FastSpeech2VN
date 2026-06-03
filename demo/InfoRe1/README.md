# InfoRe1 Demo

This folder is the Vietnamese demo area for the clean repo.

## How it is used

- place or generate paired demo WAV files
- run `scripts/build_infore1_demo.py`
- the script will copy the pairs into `samples/` and generate `manifest.json` and `index.md`

## Expected sample layout

Generated sample folders look like this:

```text
demo/InfoRe1/samples/<sample_id>/
  ground-truth.wav
  synthesized.wav
  transcript.txt
```

## Manual staging layout

If you want to stage files by hand before building the demo, use this pattern:

```text
demo/InfoRe1/inbox/<sample_id>_ground-truth.wav
demo/InfoRe1/inbox/<sample_id>_synthesized.wav
demo/InfoRe1/inbox/<sample_id>.txt
```

Then run the build script again.
