import sys
import types
import unittest

sys.modules.setdefault(
    "unidecode",
    types.SimpleNamespace(unidecode=lambda text: text),
)
sys.modules.setdefault(
    "inflect",
    types.SimpleNamespace(engine=lambda: types.SimpleNamespace(number_to_words=lambda value, **kwargs: str(value))),
)
sys.modules.setdefault(
    "torch",
    types.SimpleNamespace(save=lambda *args, **kwargs: None),
)

from scripts.check_phoneset import (
    _extract_dictionary_phone_tokens,
    _is_technical_model_symbol,
)


class CheckPhonesetTest(unittest.TestCase):
    def test_dictionary_parser_skips_numeric_metadata_columns(self):
        parts = ["hello", "0.75", "0.1", "0.2", "h", "e", "l", "o", "˧"]

        phones = _extract_dictionary_phone_tokens(parts)

        self.assertEqual(phones, ["h", "e", "l", "o", "˧"])

    def test_dictionary_parser_keeps_numeric_headword_but_not_as_phone(self):
        parts = ["13.11", "m", "ɯ", "ə", "j", "˨˩"]

        phones = _extract_dictionary_phone_tokens(parts)

        self.assertEqual(phones, ["m", "ɯ", "ə", "j", "˨˩"])

    def test_model_parser_marks_disambiguation_and_epsilon_as_technical(self):
        self.assertTrue(_is_technical_model_symbol("#17"))
        self.assertTrue(_is_technical_model_symbol("<eps>"))
        self.assertFalse(_is_technical_model_symbol("t̚"))


if __name__ == "__main__":
    unittest.main()
