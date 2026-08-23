from __future__ import annotations

import unittest

from metadata_quality.normalization import normalize_key, normalize_text, parse_positive_integer


class NormalizationTests(unittest.TestCase):
    def test_text_collapses_whitespace(self) -> None:
        self.assertEqual(normalize_text("  Deep   Orbit  "), "Deep Orbit")

    def test_key_is_case_insensitive(self) -> None:
        self.assertEqual(normalize_key(" DEEP Orbit "), "deep orbit")

    def test_positive_integer_rejects_words_and_zero(self) -> None:
        self.assertIsNone(parse_positive_integer("one"))
        self.assertIsNone(parse_positive_integer("0"))
        self.assertEqual(parse_positive_integer("2"), 2)

    def test_integer_parsing_rejects_what_python_would_silently_accept(self) -> None:
        """int() reads these as numbers. A catalog feed must not."""
        self.assertIsNone(parse_positive_integer("1_0"))
        self.assertIsNone(parse_positive_integer("+3"))
        self.assertIsNone(parse_positive_integer("٣"))
        self.assertIsNone(parse_positive_integer("3.0"))

    def test_full_width_digits_are_normalized_before_parsing(self) -> None:
        """NFKC turns full-width digits into ASCII, so they stay valid."""
        self.assertEqual(parse_positive_integer("３"), 3)


if __name__ == "__main__":
    unittest.main()

