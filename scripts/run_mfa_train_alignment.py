import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mfa', default='mfa', help='MFA executable name or path')
    parser.add_argument('--corpus-root', default='mfa_corpus/InfoRe1', help='MFA corpus directory')
    parser.add_argument('--lexicon-path', default='mfa_assets/infore1_vi.dict', help='MFA dictionary path')
    parser.add_argument('--output-root', default='preprocessed_data/InfoRe1/TextGrid', help='TextGrid output directory')
    parser.add_argument('--model-path', default='mfa_assets/infore1_vi_acoustic_model.zip', help='Exported MFA acoustic model path')
    parser.add_argument('--num-jobs', type=int, default=4, help='Number of MFA jobs')
    parser.add_argument('--single-speaker', action='store_true', help='Force single-speaker mode')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite previous MFA outputs')
    args = parser.parse_args()

    if shutil.which(args.mfa) is None:
        raise SystemExit(
            'MFA executable not found. Install Montreal Forced Aligner first, for example via conda-forge.'
        )

    corpus_root = Path(args.corpus_root)
    lexicon_path = Path(args.lexicon_path)
    output_root = Path(args.output_root)
    model_path = Path(args.model_path)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        args.mfa,
        'train',
        str(corpus_root),
        str(lexicon_path),
        str(model_path),
        '--output_directory',
        str(output_root),
        '--output_format',
        'long_textgrid',
        '--num_jobs',
        str(args.num_jobs),
        '--clean',
    ]
    if args.single_speaker:
        command.append('--single_speaker')
    if args.overwrite:
        command.append('--overwrite')

    print('Running:', ' '.join(command))
    completed = subprocess.run(command)
    sys.exit(completed.returncode)


if __name__ == '__main__':
    main()
