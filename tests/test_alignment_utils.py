import unittest
import sys
import types

sys.modules.setdefault(
    "unidecode",
    types.SimpleNamespace(unidecode=lambda text: text),
)
sys.modules.setdefault(
    "inflect",
    types.SimpleNamespace(engine=lambda: types.SimpleNamespace(number_to_words=lambda value, **kwargs: str(value))),
)

from preprocessor.alignment_utils import (
    build_alignment_settings,
    make_interval,
    sanitize_alignment_intervals,
)


class AlignmentUtilsTest(unittest.TestCase):
    def setUp(self):
        self.settings = build_alignment_settings(
            {
                "preprocessing": {
                    "alignment": {
                        "pause_phone": "sp",
                        "silence_labels": ["", "sil", "sp", "spn"],
                        "repair_zero_durations": True,
                        "drop_unrecoverable_zero_durations": True,
                        "collapse_consecutive_pauses": True,
                    }
                }
            }
        )

    def test_zero_duration_phone_is_repaired_from_neighbor(self):
        intervals = [
            make_interval(0.0, 0.1, "", 8),
            make_interval(0.1, 0.2, "m", 4),
            make_interval(0.2, 0.21, "i", 0),
            make_interval(0.21, 0.3, "˧", 6),
            make_interval(0.3, 0.4, "", 5),
        ]

        result = sanitize_alignment_intervals(intervals, self.settings)

        self.assertTrue(result["valid"])
        self.assertEqual(result["repaired_counts"]["empty_phone_normalized"], 2)
        self.assertEqual(result["repaired_counts"]["zero_duration_repaired"], 1)
        self.assertEqual([item["phone"] for item in result["intervals"]], ["m", "i", "˧"])
        self.assertEqual([item["duration"] for item in result["intervals"]], [3, 1, 6])

    def test_unrecoverable_zero_duration_phone_is_dropped(self):
        intervals = [
            make_interval(0.0, 0.1, "m", 1),
            make_interval(0.1, 0.1001, "i", 0),
            make_interval(0.1001, 0.2, "˧", 1),
        ]

        result = sanitize_alignment_intervals(intervals, self.settings)

        self.assertTrue(result["valid"])
        self.assertEqual(result["dropped_counts"]["zero_duration_unrecoverable"], 1)
        self.assertEqual([item["phone"] for item in result["intervals"]], ["m", "˧"])

    def test_overlap_is_fatal(self):
        intervals = [
            make_interval(0.0, 0.2, "m", 10),
            make_interval(0.19, 0.3, "i", 5),
        ]

        result = sanitize_alignment_intervals(intervals, self.settings)

        self.assertFalse(result["valid"])
        self.assertIn("overlap", result["fatal_errors"])


if __name__ == "__main__":
    unittest.main()
