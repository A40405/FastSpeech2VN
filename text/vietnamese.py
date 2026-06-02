import re
import unicodedata


VIETNAMESE_IPA_TOKENS = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "h",
    "i",
    "j",
    "k",
    "kʰ",
    "kw",
    "l",
    "m",
    "n",
    "o",
    "p",
    "p̚",
    "r",
    "s",
    "sp",
    "spn",
    "sil",
    "t",
    "tʰ",
    "tɕ",
    "t̚",
    "u",
    "v",
    "w",
    "x",
    "z",
    "æ",
    "ð",
    "ŋ",
    "ŋ͡m",
    "ŋ̚",
    "ɐ",
    "ɑ",
    "ɔ",
    "ə",
    "ɗ",
    "ɛ",
    "ɣ",
    "ɤ",
    "ɯ",
    "ɲ",
    "ɲ̚",
    "ʈ",
    "˧",
    "˧˥",
    "˧˥ʔ",
    "˧˩˧",
    "˨˩",
    "˨˩ʔ",
]

# Backward-compatible alias used by older imports.
VIETNAMESE_PHONE_TOKENS = VIETNAMESE_IPA_TOKENS

WORD_RE = re.compile(r"[0-9A-Za-zÀ-ỹĐđ]+|[^\s]")
DIGIT_WORDS = {
    "0": "khong",
    "1": "mot",
    "2": "hai",
    "3": "ba",
    "4": "bon",
    "5": "nam",
    "6": "sau",
    "7": "bay",
    "8": "tam",
    "9": "chin",
}
PUNCTUATION = set(",.;:!?\"'()[]{}-/")
TONE_NAMES = {
    0: "˧",
    1: "˧˥",
    2: "˨˩",
    3: "˧˩˧",
    4: "˧˥ʔ",
    5: "˨˩ʔ",
}
ACCENTED_VOWELS = {
    "a": "a",
    "á": "a",
    "à": "a",
    "ả": "a",
    "ã": "a",
    "ạ": "a",
    "ă": "ă",
    "ắ": "ă",
    "ằ": "ă",
    "ẳ": "ă",
    "ẵ": "ă",
    "ặ": "ă",
    "â": "â",
    "ấ": "â",
    "ầ": "â",
    "ẩ": "â",
    "ẫ": "â",
    "ậ": "â",
    "e": "e",
    "é": "e",
    "è": "e",
    "ẻ": "e",
    "ẽ": "e",
    "ẹ": "e",
    "ê": "ê",
    "ế": "ê",
    "ề": "ê",
    "ể": "ê",
    "ễ": "ê",
    "ệ": "ê",
    "i": "i",
    "í": "i",
    "ì": "i",
    "ỉ": "i",
    "ĩ": "i",
    "ị": "i",
    "o": "o",
    "ó": "o",
    "ò": "o",
    "ỏ": "o",
    "õ": "o",
    "ọ": "o",
    "ô": "ô",
    "ố": "ô",
    "ồ": "ô",
    "ổ": "ô",
    "ỗ": "ô",
    "ộ": "ô",
    "ơ": "ơ",
    "ớ": "ơ",
    "ờ": "ơ",
    "ở": "ơ",
    "ỡ": "ơ",
    "ợ": "ơ",
    "u": "u",
    "ú": "u",
    "ù": "u",
    "ủ": "u",
    "ũ": "u",
    "ụ": "u",
    "ư": "ư",
    "ứ": "ư",
    "ừ": "ư",
    "ử": "ư",
    "ữ": "ư",
    "ự": "ư",
    "y": "y",
    "ý": "y",
    "ỳ": "y",
    "ỷ": "y",
    "ỹ": "y",
    "ỵ": "y",
}
TONE_IDS = {
    "a": 0,
    "á": 1,
    "à": 2,
    "ả": 3,
    "ã": 4,
    "ạ": 5,
    "ă": 0,
    "ắ": 1,
    "ằ": 2,
    "ẳ": 3,
    "ẵ": 4,
    "ặ": 5,
    "â": 0,
    "ấ": 1,
    "ầ": 2,
    "ẩ": 3,
    "ẫ": 4,
    "ậ": 5,
    "e": 0,
    "é": 1,
    "è": 2,
    "ẻ": 3,
    "ẽ": 4,
    "ẹ": 5,
    "ê": 0,
    "ế": 1,
    "ề": 2,
    "ể": 3,
    "ễ": 4,
    "ệ": 5,
    "i": 0,
    "í": 1,
    "ì": 2,
    "ỉ": 3,
    "ĩ": 4,
    "ị": 5,
    "o": 0,
    "ó": 1,
    "ò": 2,
    "ỏ": 3,
    "õ": 4,
    "ọ": 5,
    "ô": 0,
    "ố": 1,
    "ồ": 2,
    "ổ": 3,
    "ỗ": 4,
    "ộ": 5,
    "ơ": 0,
    "ớ": 1,
    "ờ": 2,
    "ở": 3,
    "ỡ": 4,
    "ợ": 5,
    "u": 0,
    "ú": 1,
    "ù": 2,
    "ủ": 3,
    "ũ": 4,
    "ụ": 5,
    "ư": 0,
    "ứ": 1,
    "ừ": 2,
    "ử": 3,
    "ữ": 4,
    "ự": 5,
    "y": 0,
    "ý": 1,
    "ỳ": 2,
    "ỷ": 3,
    "ỹ": 4,
    "ỵ": 5,
}
ONSET_MAP = [
    ("ngh", "ŋ"),
    ("ng", "ŋ"),
    ("gh", "ɣ"),
    ("gi", "z"),
    ("qu", "kw"),
    ("th", "tʰ"),
    ("tr", "ʈ"),
    ("ph", "f"),
    ("nh", "ɲ"),
    ("ch", "tɕ"),
    ("kh", "x"),
    ("b", "b"),
    ("c", "k"),
    ("d", "z"),
    ("đ", "ɗ"),
    ("g", "ɣ"),
    ("h", "h"),
    ("k", "k"),
    ("l", "l"),
    ("m", "m"),
    ("n", "n"),
    ("p", "p"),
    ("q", "kw"),
    ("r", "r"),
    ("s", "s"),
    ("t", "t"),
    ("v", "v"),
    ("x", "s"),
]
CODA_MAP = [
    ("nh", "ɲ̚"),
    ("ng", "ŋ̚"),
    ("ch", "k̚"),
    ("c", "k̚"),
    ("m", "m"),
    ("n", "n"),
    ("p", "p̚"),
    ("t", "t̚"),
    ("y", "j"),
    ("i", "j"),
    ("u", "w"),
    ("o", "w"),
]
VOWEL_MAP = {
    "a": "a",
    "ă": "ɐ",
    "â": "ə",
    "e": "ɛ",
    "ê": "e",
    "i": "i",
    "y": "i",
    "o": "ɔ",
    "ô": "o",
    "ơ": "ɤ",
    "u": "u",
    "ư": "ɯ",
}


def normalize_text(text):
    return unicodedata.normalize("NFC", text.strip().lower())


def strip_tone(word):
    tone = 0
    base_chars = []
    for char in normalize_text(word):
        if char in TONE_IDS:
            tone = max(tone, TONE_IDS[char])
            base_chars.append(ACCENTED_VOWELS[char])
        else:
            base_chars.append(char)
    return "".join(base_chars), tone


def split_onset(word):
    for prefix, token in ONSET_MAP:
        if word.startswith(prefix):
            remainder = word[len(prefix) :]
            if prefix == "gi" and remainder == "":
                remainder = "i"
            return token, remainder
    return None, word


def split_coda(word):
    for suffix, token in CODA_MAP:
        if word.endswith(suffix) and len(word) > len(suffix):
            return word[: -len(suffix)], token
    return word, None


def word_to_ipa_tokens(word):
    if not word:
        return []

    if all(char.isdigit() for char in word):
        tokens = []
        for idx, digit in enumerate(word):
            tokens.extend(word_to_ipa_tokens(DIGIT_WORDS.get(digit, "")))
            if idx != len(word) - 1:
                tokens.append("sp")
        return tokens

    normalized, tone = strip_tone(word)
    onset_token, remainder = split_onset(normalized)
    vowel_chunk, coda_token = split_coda(remainder)

    tokens = []
    if onset_token:
        tokens.append(onset_token)

    for char in vowel_chunk:
        mapped = VOWEL_MAP.get(char)
        if mapped is not None:
            tokens.append(mapped)

    if not any(token in VOWEL_MAP.values() for token in tokens):
        return ["spn"]

    if coda_token:
        tokens.append(coda_token)

    tokens.append(TONE_NAMES[tone])
    return tokens


def word_to_phoneme_tokens(word):
    return word_to_ipa_tokens(word)


def phonemize_text(text):
    tokens = []
    for piece in WORD_RE.findall(normalize_text(text)):
        if piece in PUNCTUATION:
            if not tokens or tokens[-1] != "sp":
                tokens.append("sp")
            continue

        tokens.extend(word_to_ipa_tokens(piece))

    while tokens and tokens[-1] == "sp":
        tokens.pop()
    return tokens or ["spn"]
