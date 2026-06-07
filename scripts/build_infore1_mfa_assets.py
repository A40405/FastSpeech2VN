import argparse
import csv
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from text.vietnamese import (
    MFA_PHONE_COVERAGE_SEEDS,
    PAUSE_WORD,
    iter_symbol_mapping_rows,
    normalize_text,
    text_to_training_units,
    word_to_phoneme_tokens,
)


def link_or_copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def write_lexicon(lexicon, lexicon_path):
    lexicon_path.parent.mkdir(parents=True, exist_ok=True)
    with lexicon_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("<unk> spn\n")
        f.write(f"{PAUSE_WORD} sp\n")
        for word in sorted(lexicon):
            f.write(f"{word} {' '.join(lexicon[word])}\n")


def write_wordlist(lexicon, wordlist_path):
    wordlist_path.parent.mkdir(parents=True, exist_ok=True)
    with wordlist_path.open("w", encoding="utf-8", newline="\n") as f:
        for word in sorted(lexicon):
            f.write(f"{word}\n")


def write_g2p_training_data(lexicon, g2p_train_path):
    g2p_train_path.parent.mkdir(parents=True, exist_ok=True)
    with g2p_train_path.open("w", encoding="utf-8", newline="\n") as f:
        for word in sorted(lexicon):
            f.write(f"{word}\t{' '.join(lexicon[word])}\n")


def write_symbol_map(symbol_map_path):
    symbol_map_path.parent.mkdir(parents=True, exist_ok=True)
    with symbol_map_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["ipa_phone", "fastspeech_symbol", "category"])
        for row in iter_symbol_mapping_rows():
            writer.writerow(row)


def build_augmented_lexicon(corpus_lexicon):
    augmented = dict(corpus_lexicon)
    covered_phones = {phone for phones in augmented.values() for phone in phones}
    added_seeds = {}

    for seed_word, phones in MFA_PHONE_COVERAGE_SEEDS.items():
        if not any(phone not in covered_phones for phone in phones):
            continue
        augmented[seed_word] = list(phones)
        added_seeds[seed_word] = list(phones)
        covered_phones.update(phones)

    return augmented, added_seeds


def build_assets(
    raw_root,
    corpus_root,
    lexicon_path,
    g2p_train_path,
    wordlist_path,
    symbol_map_path,
):
    raw_root = Path(raw_root)
    corpus_root = Path(corpus_root)
    lexicon_path = Path(lexicon_path)
    g2p_train_path = Path(g2p_train_path)
    wordlist_path = Path(wordlist_path)
    symbol_map_path = Path(symbol_map_path)

    lexicon = {}
    utterance_count = 0

    for speaker_dir in sorted(p for p in raw_root.iterdir() if p.is_dir()):
        speaker_out = corpus_root / speaker_dir.name
        speaker_out.mkdir(parents=True, exist_ok=True)

        for wav_path in sorted(speaker_dir.glob("*.wav")):
            lab_path = wav_path.with_suffix(".lab")
            if not lab_path.exists():
                continue

            raw_text = lab_path.read_text(encoding="utf-8").strip()
            units = text_to_training_units(raw_text)
            if not units:
                continue

            normalized_transcript = " ".join(
                unit if unit == PAUSE_WORD else normalize_text(unit) for unit in units
            )
            out_wav_path = speaker_out / wav_path.name
            out_lab_path = speaker_out / f"{wav_path.stem}.lab"
            link_or_copy(wav_path, out_wav_path)
            out_lab_path.write_text(normalized_transcript, encoding="utf-8")
            utterance_count += 1

            for word in units:
                if word == PAUSE_WORD:
                    continue
                normalized_word = normalize_text(word)
                if normalized_word not in lexicon:
                    phones = word_to_phoneme_tokens(normalized_word)
                    lexicon[normalized_word] = phones if phones else ["spn"]

    augmented_lexicon, added_seed_lexicon = build_augmented_lexicon(lexicon)

    write_lexicon(augmented_lexicon, lexicon_path)
    write_wordlist(lexicon, wordlist_path)
    write_g2p_training_data(augmented_lexicon, g2p_train_path)
    write_symbol_map(symbol_map_path)

    print(f"Prepared MFA corpus: {corpus_root}")
    print(f"Prepared lexicon: {lexicon_path}")
    print(f"Prepared G2P training data: {g2p_train_path}")
    print(f"Prepared word list: {wordlist_path}")
    print(f"Prepared symbol map: {symbol_map_path}")
    print(f"Utterances: {utterance_count}")
    print(f"Vocabulary size: {len(lexicon)}")
    print(f"Coverage seeds added: {len(added_seed_lexicon)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", default="raw_data/InfoRe1", help="Prepared raw corpus root")
    parser.add_argument("--corpus-root", default="mfa_corpus/InfoRe1", help="Output corpus directory for MFA")
    parser.add_argument("--lexicon-path", default="mfa_assets/infore1_vi.dict", help="Output pronunciation dictionary path")
    parser.add_argument(
        "--g2p-train-path",
        default="mfa_assets/infore1_vi_g2p.tsv",
        help="Output G2P training data in word<TAB>phones format",
    )
    parser.add_argument(
        "--wordlist-path",
        default="mfa_assets/infore1_vi.wordlist",
        help="Output normalized word list for MFA G2P inference",
    )
    parser.add_argument(
        "--symbol-map-path",
        default="mfa_assets/infore1_vi_symbol_map.tsv",
        help="Output mapping between IPA phones and FastSpeech2 symbols",
    )
    args = parser.parse_args()
    build_assets(
        args.raw_root,
        args.corpus_root,
        args.lexicon_path,
        args.g2p_train_path,
        args.wordlist_path,
        args.symbol_map_path,
    )
