import re
from pathlib import Path
from typing import Dict, List


NUMERIC_TOKEN_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d+)?|\.\d+)$")


def is_numeric_token(token: str) -> bool:
    return bool(NUMERIC_TOKEN_RE.match(token))


def extract_mfa_dictionary_phones(parts: List[str]) -> List[str]:
    if len(parts) < 2:
        return []

    phone_start = 1
    while phone_start < len(parts) and is_numeric_token(parts[phone_start]):
        phone_start += 1

    return [token for token in parts[phone_start:] if token and not is_numeric_token(token)]


def read_mfa_lexicon(lex_path: Path) -> Dict[str, List[str]]:
    lexicon: Dict[str, List[str]] = {}
    if not lex_path.exists():
        return lexicon

    with lex_path.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue

            word = parts[0].lower()
            phones = extract_mfa_dictionary_phones(parts)
            if word and phones and word not in lexicon:
                lexicon[word] = phones

    return lexicon
