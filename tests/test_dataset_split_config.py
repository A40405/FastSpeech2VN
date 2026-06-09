import unittest

from utils.splits import get_split_filename


class DatasetSplitConfigTest(unittest.TestCase):
    def test_defaults_to_standard_split_names(self):
        train_config = {}

        self.assertEqual(get_split_filename(train_config, "train"), "train.txt")
        self.assertEqual(get_split_filename(train_config, "val"), "val.txt")

    def test_reads_split_names_from_train_config(self):
        train_config = {
            "dataset": {
                "train_file": "train.clean.txt",
                "val_file": "val.clean.txt",
            }
        }

        self.assertEqual(get_split_filename(train_config, "train"), "train.clean.txt")
        self.assertEqual(get_split_filename(train_config, "val"), "val.clean.txt")


if __name__ == "__main__":
    unittest.main()
