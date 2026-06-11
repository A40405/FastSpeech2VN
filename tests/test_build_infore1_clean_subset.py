import sys
import types
import unittest

sys.modules.setdefault(
    "torch",
    types.SimpleNamespace(save=lambda *args, **kwargs: None),
)

from scripts.build_infore1_clean_subset import evaluate_sample, select_records


class BuildCleanSubsetTest(unittest.TestCase):
    def setUp(self):
        self.thresholds = {
            "min_total_duration_frames": 48,
            "max_zero_duration_repaired": 0,
            "max_one_frame_non_silence_count": 10,
            "max_one_frame_non_silence_ratio": 0.10,
            "max_pause_frame_ratio": 0.25,
            "max_token_count": 110,
            "max_samples_per_split": 0,
        }

    def test_evaluate_sample_keeps_clean_record(self):
        sample = {
            "fatal_errors": [],
            "drop_reason": None,
            "repaired_counts": {"zero_duration_repaired": 0},
            "quality_metrics": {
                "total_duration_frames": 64,
                "one_frame_non_silence_count": 2,
                "one_frame_non_silence_ratio": 0.04,
                "pause_frame_ratio": 0.11,
            },
            "token_count": 48,
        }

        keep, reason = evaluate_sample(sample, self.thresholds)

        self.assertTrue(keep)
        self.assertEqual(reason, "kept")

    def test_evaluate_sample_drops_high_pause_ratio(self):
        sample = {
            "fatal_errors": [],
            "drop_reason": None,
            "repaired_counts": {"zero_duration_repaired": 0},
            "quality_metrics": {
                "total_duration_frames": 64,
                "one_frame_non_silence_count": 2,
                "one_frame_non_silence_ratio": 0.04,
                "pause_frame_ratio": 0.31,
            },
            "token_count": 48,
        }

        keep, reason = evaluate_sample(sample, self.thresholds)

        self.assertFalse(keep)
        self.assertEqual(reason, "pause_frame_ratio")

    def test_select_records_ranks_cleaner_samples_first(self):
        records = [
            {
                "line": "0001|InfoRe1|{a}|xin chào bạn",
                "basename": "0001",
                "speaker": "InfoRe1",
                "text": "{a}",
                "raw_text": "xin chào bạn",
            },
            {
                "line": "0002|InfoRe1|{b}|mời bạn ngồi xuống",
                "basename": "0002",
                "speaker": "InfoRe1",
                "text": "{b}",
                "raw_text": "mời bạn ngồi xuống",
            },
        ]
        indexed_report = {
            ("InfoRe1", "0001"): {
                "fatal_errors": [],
                "drop_reason": None,
                "repaired_counts": {"zero_duration_repaired": 0},
                "token_count": 48,
                "quality_metrics": {
                    "total_duration_frames": 90,
                    "one_frame_non_silence_count": 1,
                    "one_frame_non_silence_ratio": 0.02,
                    "pause_frame_ratio": 0.08,
                },
            },
            ("InfoRe1", "0002"): {
                "fatal_errors": [],
                "drop_reason": None,
                "repaired_counts": {"zero_duration_repaired": 0},
                "token_count": 48,
                "quality_metrics": {
                    "total_duration_frames": 70,
                    "one_frame_non_silence_count": 3,
                    "one_frame_non_silence_ratio": 0.09,
                    "pause_frame_ratio": 0.18,
                },
            },
        }
        thresholds = dict(self.thresholds)
        thresholds["max_samples_per_split"] = 1

        kept, dropped_counts, missing = select_records(
            records, indexed_report, thresholds
        )

        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["record"]["basename"], "0001")
        self.assertEqual(dropped_counts["trimmed_after_ranking"], 1)
        self.assertEqual(missing, [])

    def test_evaluate_sample_drops_overlong_sequence(self):
        sample = {
            "fatal_errors": [],
            "drop_reason": None,
            "repaired_counts": {"zero_duration_repaired": 0},
            "token_count": 111,
            "quality_metrics": {
                "total_duration_frames": 120,
                "one_frame_non_silence_count": 2,
                "one_frame_non_silence_ratio": 0.02,
                "pause_frame_ratio": 0.05,
            },
        }

        keep, reason = evaluate_sample(sample, self.thresholds)

        self.assertFalse(keep)
        self.assertEqual(reason, "token_count")


if __name__ == "__main__":
    unittest.main()
