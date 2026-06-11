import sys
import types
import unittest

sys.modules.setdefault(
    "unidecode",
    types.SimpleNamespace(unidecode=lambda text: text),
)
sys.modules.setdefault(
    "inflect",
    types.SimpleNamespace(
        engine=lambda: types.SimpleNamespace(
            number_to_words=lambda value, **kwargs: str(value)
        )
    ),
)

from scripts.build_infore1_mfa_assets import build_augmented_lexicon
from text.vietnamese import MFA_PHONE_COVERAGE_SEEDS, word_to_phoneme_tokens


class BuildMfaAssetsTest(unittest.TestCase):
    def test_missing_frontend_phones_get_seed_entries(self):
        corpus_lexicon = {
            "ba": ["b", "a", "˧"],
            "da": ["z", "a", "˧"],
        }

        augmented, added = build_augmented_lexicon(corpus_lexicon)

        self.assertIn("__cov_phone_c__", added)
        self.assertIn("__cov_phone_sil__", added)
        self.assertEqual(augmented["__cov_phone_c__"], ["c"])
        self.assertEqual(augmented["__cov_phone_sil__"], ["sil"])
        self.assertEqual(augmented["ba"], ["b", "a", "˧"])

    def test_existing_phone_seed_is_not_added_twice(self):
        corpus_lexicon = {
            "cov": ["c", "d", "kʰ", "sil", "æ", "ð", "ŋ͡m", "ɑ"],
        }

        augmented, added = build_augmented_lexicon(corpus_lexicon)

        self.assertEqual(augmented, corpus_lexicon)
        self.assertEqual(added, {})
        self.assertTrue(MFA_PHONE_COVERAGE_SEEDS)

    def test_ascii_abbreviation_spells_out_instead_of_spn(self):
        tp_tokens = word_to_phoneme_tokens("tp")
        hcm_tokens = word_to_phoneme_tokens("hcm")

        self.assertNotEqual(tp_tokens, ["spn"])
        self.assertNotEqual(hcm_tokens, ["spn"])
        self.assertTrue(tp_tokens)
        self.assertTrue(hcm_tokens)


if __name__ == "__main__":
    unittest.main()
