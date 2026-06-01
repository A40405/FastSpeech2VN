import re
import unicodedata


VIETNAMESE_PHONE_TOKENS = [
    "on_b",
    "on_ch",
    "on_dd",
    "on_f",
    "on_g",
    "on_h",
    "on_k",
    "on_kh",
    "on_kw",
    "on_l",
    "on_m",
    "on_n",
    "on_ng",
    "on_nh",
    "on_p",
    "on_r",
    "on_s",
    "on_t",
    "on_th",
    "on_tr",
    "on_v",
    "on_x",
    "on_z",
    "v_a",
    "v_aa",
    "v_aw",
    "v_e",
    "v_ee",
    "v_i",
    "v_o",
    "v_oo",
    "v_ow",
    "v_u",
    "v_uw",
    "cod_j",
    "cod_k",
    "cod_m",
    "cod_n",
    "cod_ng",
    "cod_nh",
    "cod_p",
    "cod_t",
    "cod_w",
    "tone_ngang",
    "tone_sac",
    "tone_huyen",
    "tone_hoi",
    "tone_nga",
    "tone_nang",
    "sp",
    "spn",
    "sil",
]


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
    0: "tone_ngang",
    1: "tone_sac",
    2: "tone_huyen",
    3: "tone_hoi",
    4: "tone_nga",
    5: "tone_nang",
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
    ("ngh", "on_ng"),
    ("ng", "on_ng"),
    ("gh", "on_g"),
    ("gi", "on_z"),
    ("qu", "on_kw"),
    ("th", "on_th"),
    ("tr", "on_tr"),
    ("ph", "on_f"),
    ("nh", "on_nh"),
    ("ch", "on_ch"),
    ("kh", "on_kh"),
    ("b", "on_b"),
    ("c", "on_k"),
    ("d", "on_z"),
    ("đ", "on_dd"),
    ("g", "on_g"),
    ("h", "on_h"),
    ("k", "on_k"),
    ("l", "on_l"),
    ("m", "on_m"),
    ("n", "on_n"),
    ("p", "on_p"),
    ("q", "on_kw"),
    ("r", "on_r"),
    ("s", "on_s"),
    ("t", "on_t"),
    ("v", "on_v"),
    ("x", "on_x"),
]
CODA_MAP = [
    ("nh", "cod_nh"),
    ("ng", "cod_ng"),
    ("ch", "cod_k"),
    ("c", "cod_k"),
    ("m", "cod_m"),
    ("n", "cod_n"),
    ("p", "cod_p"),
    ("t", "cod_t"),
    ("y", "cod_j"),
    ("i", "cod_j"),
    ("u", "cod_w"),
    ("o", "cod_w"),
]
VOWEL_MAP = {
    "a": "v_a",
    "ă": "v_aw",
    "â": "v_aa",
    "e": "v_e",
    "ê": "v_ee",
    "i": "v_i",
    "y": "v_i",
    "o": "v_o",
    "ô": "v_oo",
    "ơ": "v_ow",
    "u": "v_u",
    "ư": "v_uw",
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


def word_to_phoneme_tokens(word):
    if not word:
        return []

    if all(char.isdigit() for char in word):
        tokens = []
        for idx, digit in enumerate(word):
            tokens.extend(word_to_phoneme_tokens(DIGIT_WORDS.get(digit, "")))
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
        if char in VOWEL_MAP:
            tokens.append(VOWEL_MAP[char])

    if not any(token.startswith("v_") for token in tokens):
        return ["spn"]

    if coda_token:
        tokens.append(coda_token)

    tokens.append(TONE_NAMES[tone])
    return tokens


def phonemize_text(text):
    tokens = []
    for piece in WORD_RE.findall(normalize_text(text)):
        if piece in PUNCTUATION:
            if not tokens or tokens[-1] != "sp":
                tokens.append("sp")
            continue

        word_tokens = word_to_phoneme_tokens(piece)
        tokens.extend(word_tokens)

    while tokens and tokens[-1] == "sp":
        tokens.pop()
    return tokens or ["spn"]

