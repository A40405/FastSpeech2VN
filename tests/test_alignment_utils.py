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
    assess_alignment_quality,
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

    def test_quality_report_drops_sample_with_too_many_one_frame_phones(self):
        intervals = [
            make_interval(0.0, 0.1, "m", 20),
            make_interval(0.1, 0.2, "a", 1),
            make_interval(0.2, 0.3, "n", 1),
            make_interval(0.3, 0.4, "˧", 1),
            make_interval(0.4, 0.5, "t", 1),
            make_interval(0.5, 0.6, "a", 1),
        ]

        result = sanitize_alignment_intervals(intervals, self.settings)
        quality = assess_alignment_quality(result, self.settings)

        self.assertEqual(
            quality["drop_reason"], "high_one_frame_non_silence_ratio"
        )
        self.assertIn(
            "high_one_frame_non_silence_ratio", quality["quality_issues"]
        )

    def test_quality_report_drops_sample_with_too_many_zero_repairs(self):
        intervals = [
            make_interval(0.0, 0.1, "m", 14),
            make_interval(0.1, 0.11, "a", 0),
            make_interval(0.11, 0.12, "n", 0),
            make_interval(0.12, 0.13, "˧", 0),
            make_interval(0.13, 0.3, "t", 14),
        ]

        result = sanitize_alignment_intervals(intervals, self.settings)
        quality = assess_alignment_quality(result, self.settings)

        self.assertEqual(
            quality["drop_reason"], "high_zero_duration_repaired_ratio"
        )
        self.assertIn(
            "high_zero_duration_repaired_ratio", quality["quality_issues"]
        )


if __name__ == "__main__":
    unittest.main()
