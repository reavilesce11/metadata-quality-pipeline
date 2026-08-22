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


if __name__ == "__main__":
    unittest.main()

