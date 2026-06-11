import unittest

from utils.tools import sanitize_filename


class ToolsTest(unittest.TestCase):
    def test_sanitize_filename_removes_windows_invalid_characters(self):
        self.assertEqual(
            sanitize_filename('xin chào bạn, hôm nay trời đẹp quá phải không?'),
            "xin chào bạn, hôm nay trời đẹp quá phải không_",
        )

    def test_sanitize_filename_trims_trailing_dots_and_spaces(self):
        self.assertEqual(sanitize_filename("sample. "), "sample")

    def test_sanitize_filename_returns_fallback_for_empty_result(self):
        self.assertEqual(sanitize_filename("???"), "sample")


if __name__ == "__main__":
    unittest.main()
