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
    "k̚",
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
FASTSPEECH_SYMBOL_PREFIX = "@"

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
PAUSE_PUNCTUATION = set(",.;:!?")
PAUSE_WORD = "<sp>"
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


ONSET_IPA_TOKENS = sorted({token for _, token in ONSET_MAP})
VOWEL_IPA_TOKENS = sorted(set(VOWEL_MAP.values()))
CODA_IPA_TOKENS = sorted({token for _, token in CODA_MAP})
TONE_IPA_TOKENS = [TONE_NAMES[idx] for idx in sorted(TONE_NAMES)]
SILENCE_IPA_TOKENS = ["sp", "spn", "sil"]
DEFAULT_PAUSE_PHONE = "sp"
DEFAULT_ALIGNMENT_SILENCE_LABELS = ["", *SILENCE_IPA_TOKENS]


TOKEN_CATEGORY_MAP = {}
for token in ONSET_IPA_TOKENS:
    TOKEN_CATEGORY_MAP[token] = "onset"
for token in VOWEL_IPA_TOKENS:
    TOKEN_CATEGORY_MAP[token] = "vowel"
for token in CODA_IPA_TOKENS:
    TOKEN_CATEGORY_MAP[token] = "coda"
for token in TONE_IPA_TOKENS:
    TOKEN_CATEGORY_MAP[token] = "tone"
for token in SILENCE_IPA_TOKENS:
    TOKEN_CATEGORY_MAP[token] = "special"


FASTSPEECH_SYMBOL_MAP = {
    token: f"{FASTSPEECH_SYMBOL_PREFIX}{token}" for token in VIETNAMESE_IPA_TOKENS
}

# ASCII abbreviations and letter-by-letter spellings appear frequently in real
# Vietnamese text (for example: TP, HCM, UBND). If the direct Vietnamese word
# pronunciation fails, we fall back to a deterministic spelling pronunciation so
# those items do not collapse to spn in MFA/G2P assets.
ASCII_LETTER_SPELLINGS = {
    "a": "a",
    "b": "bê",
    "c": "xê",
    "d": "dê",
    "e": "e",
    "f": "ép",
    "g": "giê",
    "h": "hát",
    "i": "i",
    "j": "giê",
    "k": "ca",
    "l": "e lờ",
    "m": "em",
    "n": "en",
    "o": "o",
    "p": "pê",
    "q": "quy",
    "r": "rờ",
    "s": "ét",
    "t": "tê",
    "u": "u",
    "v": "vê",
    "w": "vê kép",
    "x": "ích",
    "y": "i dài",
    "z": "dét",
}

# Synthetic lexicon/G2P seeds keep rarely used frontend symbols reachable in MFA assets
# without polluting real transcript text or corpus-derived word lists.
MFA_PHONE_COVERAGE_SEEDS = {
    "__cov_phone_c__": ["c"],
    "__cov_phone_d__": ["d"],
    "__cov_phone_kh__": ["kʰ"],
    "__cov_phone_sil__": ["sil"],
    "__cov_phone_ae__": ["æ"],
    "__cov_phone_eth__": ["ð"],
    "__cov_phone_ngm__": ["ŋ͡m"],
    "__cov_phone_opena__": ["ɑ"],
}


def normalize_text(text):
    return unicodedata.normalize("NFC", text.strip().lower())


def _read_two_digits(number, full=False):
    tens = number // 10
    units = number % 10
    words = []

    if tens == 0:
        if units == 0:
            return words
        if full:
            words.append("linh")
        words.append(DIGIT_WORDS[str(units)])
        return words

    if tens == 1:
        words.append("muoi")
    else:
        words.extend([DIGIT_WORDS[str(tens)], "muoi"])

    if units == 0:
        return words
    if units == 5:
        words.append("lam")
    else:
        words.append(DIGIT_WORDS[str(units)])
    return words


def _read_three_digits(number, full=False):
    hundreds = number // 100
    remainder = number % 100
    words = []

    if hundreds > 0:
        words.extend([DIGIT_WORDS[str(hundreds)], "tram"])
        words.extend(_read_two_digits(remainder, full=remainder > 0))
        return words

    if full and remainder > 0:
        words.extend(["khong", "tram"])
        words.extend(_read_two_digits(remainder, full=True))
        return words

    return _read_two_digits(remainder, full=False)


def number_to_words(number_text):
    if not number_text:
        return []
    if len(number_text) > 1 and number_text.startswith("0"):
        return [DIGIT_WORDS[digit] for digit in number_text if digit in DIGIT_WORDS]

    number = int(number_text)
    if number == 0:
        return [DIGIT_WORDS["0"]]

    unit_names = ["", "nghin", "trieu", "ty", "nghin ty", "trieu ty"]
    groups = []
    while number > 0:
        groups.append(number % 1000)
        number //= 1000

    words = []
    highest = len(groups) - 1
    for idx in range(highest, -1, -1):
        group = groups[idx]
        if group == 0:
            continue
        full = idx != highest and group < 100
        group_words = _read_three_digits(group, full=full)
        words.extend(group_words)
        unit_name = unit_names[idx] if idx < len(unit_names) else ""
        if unit_name:
            words.append(unit_name)
    return words


def text_to_units(text, preserve_pauses=False):
    words = []
    for piece in WORD_RE.findall(normalize_text(text)):
        if piece in PUNCTUATION:
            if preserve_pauses and piece in PAUSE_PUNCTUATION:
                if words and words[-1] != PAUSE_WORD:
                    words.append(PAUSE_WORD)
            continue
        if piece.isdigit():
            words.extend(number_to_words(piece))
            continue
        words.append(piece)
    if preserve_pauses:
        while words and words[-1] == PAUSE_WORD:
            words.pop()
    return words


def text_to_words(text):
    return text_to_units(text, preserve_pauses=False)


def text_to_training_units(text):
    return text_to_units(text, preserve_pauses=True)


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


def _spell_ascii_abbreviation(word):
    if not word or not word.isascii() or not word.isalpha():
        return None

    spoken_words = []
    for char in word:
        spelled = ASCII_LETTER_SPELLINGS.get(char)
        if spelled is None:
            return None
        spoken_words.append(spelled)

    return words_to_phone_tokens(text_to_training_units(" ".join(spoken_words)))


def word_to_ipa_tokens(word):
    if not word:
        return []

    if word == PAUSE_WORD:
        return ["sp"]

    if all(char.isdigit() for char in word):
        tokens = []
        for spoken_word in number_to_words(word):
            tokens.extend(word_to_ipa_tokens(spoken_word))
        return tokens or ["spn"]

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
        spelled_tokens = _spell_ascii_abbreviation(normalized)
        if spelled_tokens:
            return spelled_tokens
        return ["spn"]

    if coda_token:
        tokens.append(coda_token)

    tokens.append(TONE_NAMES[tone])
    return tokens


def word_to_phoneme_tokens(word):
    return word_to_ipa_tokens(word)


def words_to_phone_tokens(words):
    tokens = []
    for word in words:
        normalized_word = normalize_text(word)
        if normalized_word:
            tokens.extend(word_to_phoneme_tokens(normalized_word))
    return tokens or ["spn"]


def text_to_phone_tokens(text):
    return words_to_phone_tokens(text_to_training_units(text))


def phones_to_fastspeech_symbols(phones):
    return [FASTSPEECH_SYMBOL_MAP[phone] for phone in phones if phone in FASTSPEECH_SYMBOL_MAP]


def iter_symbol_mapping_rows():
    for token in VIETNAMESE_IPA_TOKENS:
        yield token, FASTSPEECH_SYMBOL_MAP[token], TOKEN_CATEGORY_MAP.get(token, "other")


def phonemize_text(text):
    return words_to_phone_tokens(text_to_training_units(text))
