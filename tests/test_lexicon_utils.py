import unittest
import uuid
from pathlib import Path

from utils.lexicon import extract_mfa_dictionary_phones, read_mfa_lexicon

TEST_TMP_ROOT = Path(__file__).resolve().parent / ".tmp"


class LexiconUtilsTest(unittest.TestCase):
    def test_extract_mfa_dictionary_phones_skips_numeric_scores(self):
        parts = ["xin", "0.99", "0.1", "0.68", "1.15", "s", "i", "n", "˧"]
        self.assertEqual(extract_mfa_dictionary_phones(parts), ["s", "i", "n", "˧"])

    def test_read_mfa_lexicon_keeps_plain_dictionary_rows(self):
        TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
        lexicon_path = TEST_TMP_ROOT / f"plain-{uuid.uuid4().hex}.dict"
        try:
            lexicon_path.write_text("<sp>\tsp\nxin\ts i n ˧\n", encoding="utf-8")

            lexicon = read_mfa_lexicon(lexicon_path)

            self.assertEqual(lexicon["<sp>"], ["sp"])
            self.assertEqual(lexicon["xin"], ["s", "i", "n", "˧"])
        finally:
            if lexicon_path.exists():
                lexicon_path.unlink()

    def test_read_mfa_lexicon_strips_numeric_scores_from_mfa_rows(self):
        TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
        lexicon_path = TEST_TMP_ROOT / f"scored-{uuid.uuid4().hex}.dict"
        try:
            lexicon_path.write_text(
                "xin\t0.99\t0.1\t0.68\t1.15\ts i n ˧\n"
                "chao\t0.99\t0.15\t1.51\t0.75\ttɕ a w ˨˩\n",
                encoding="utf-8",
            )

            lexicon = read_mfa_lexicon(lexicon_path)

            self.assertEqual(lexicon["xin"], ["s", "i", "n", "˧"])
            self.assertEqual(lexicon["chao"], ["tɕ", "a", "w", "˨˩"])
        finally:
            if lexicon_path.exists():
                lexicon_path.unlink()


if __name__ == "__main__":
    unittest.main()
