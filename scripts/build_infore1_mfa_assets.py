import argparse
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from text.vietnamese import DIGIT_WORDS, PUNCTUATION, WORD_RE, normalize_text, word_to_phoneme_tokens

def text_to_words(text):
    words = []
    for piece in WORD_RE.findall(normalize_text(text)):
        if piece in PUNCTUATION:
            continue
        if piece.isdigit():
            for digit in piece:
                spoken = DIGIT_WORDS.get(digit)
                if spoken:
                    words.append(spoken)
            continue
        words.append(piece)
    return words


def link_or_copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def build_assets(raw_root, corpus_root, lexicon_path):
    raw_root = Path(raw_root)
    corpus_root = Path(corpus_root)
    lexicon_path = Path(lexicon_path)
    lexicon_path.parent.mkdir(parents=True, exist_ok=True)

    lexicon = {}
    utterance_count = 0

    for speaker_dir in sorted(p for p in raw_root.iterdir() if p.is_dir()):
        speaker_out = corpus_root / speaker_dir.name
        speaker_out.mkdir(parents=True, exist_ok=True)

        for wav_path in sorted(speaker_dir.glob('*.wav')):
            lab_path = wav_path.with_suffix('.lab')
            if not lab_path.exists():
                continue

            raw_text = lab_path.read_text(encoding='utf-8').strip()
            words = text_to_words(raw_text)
            if not words:
                continue

            normalized_transcript = ' '.join(words)
            out_wav_path = speaker_out / wav_path.name
            out_lab_path = speaker_out / f'{wav_path.stem}.lab'
            link_or_copy(wav_path, out_wav_path)
            out_lab_path.write_text(normalized_transcript, encoding='utf-8')
            utterance_count += 1

            for word in words:
                if word not in lexicon:
                    phones = word_to_phoneme_tokens(word)
                    lexicon[word] = phones if phones else ['spn']

    with lexicon_path.open('w', encoding='utf-8', newline='\n') as f:
        f.write('<unk> spn\n')
        for word in sorted(lexicon):
            f.write(f"{word} {' '.join(lexicon[word])}\n")

    print(f'Prepared MFA corpus: {corpus_root}')
    print(f'Prepared lexicon: {lexicon_path}')
    print(f'Utterances: {utterance_count}')
    print(f'Vocabulary size: {len(lexicon)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-root', default='raw_data/InfoRe1', help='Prepared raw corpus root')
    parser.add_argument('--corpus-root', default='mfa_corpus/InfoRe1', help='Output corpus directory for MFA')
    parser.add_argument('--lexicon-path', default='mfa_assets/infore1_vi.dict', help='Output pronunciation dictionary path')
    args = parser.parse_args()
    build_assets(args.raw_root, args.corpus_root, args.lexicon_path)
