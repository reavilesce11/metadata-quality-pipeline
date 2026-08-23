from __future__ import annotations

import unittest

from metadata_quality.quality import validate_record


class QualityRuleTests(unittest.TestCase):
    def test_invalid_structure_creates_stable_issue_codes(self) -> None:
        row = {
            "provider_record_id": "P100",
            "series_title": "Deep Orbit",
            "season_number": "one",
            "episode_number": "0",
            "episode_title": "",
            "air_date": "2026-31-01",
            "duration_minutes": "-5",
        }
        issues = validate_record(row, 2)
        codes = {issue.issue_code for issue in issues}
        self.assertEqual(
            codes,
            {
                "INVALID_POSITIVE_INTEGER",
                "INVALID_ISO_DATE",
                "IMPLAUSIBLE_DURATION",
                "EPISODE_TITLE_MISSING",
            },
        )
        self.assertEqual(sum(issue.severity == "ERROR" for issue in issues), 3)

    def test_air_date_must_use_the_documented_format(self) -> None:
        """date.fromisoformat accepts more than YYYY-MM-DD since Python 3.11."""
        for value in ("20260131", "2026-W05-1", "2026/01/31", "31-01-2026"):
            with self.subTest(air_date=value):
                row = {
                    "provider_record_id": "P200",
                    "series_title": "Deep Orbit",
                    "season_number": "1",
                    "episode_number": "1",
                    "episode_title": "First Light",
                    "air_date": value,
                    "duration_minutes": "47",
                }
                codes = {issue.issue_code for issue in validate_record(row, 1)}
                self.assertIn("INVALID_ISO_DATE", codes)

    def test_a_correct_calendar_date_raises_no_issue(self) -> None:
        row = {
            "provider_record_id": "P201",
            "series_title": "Deep Orbit",
            "season_number": "1",
            "episode_number": "1",
            "episode_title": "First Light",
            "air_date": "2026-01-05",
            "duration_minutes": "47",
        }
        self.assertEqual(validate_record(row, 1), [])

    def test_an_impossible_calendar_day_is_still_rejected(self) -> None:
        row = {
            "provider_record_id": "P202",
            "series_title": "Deep Orbit",
            "season_number": "1",
            "episode_number": "1",
            "episode_title": "First Light",
            "air_date": "2026-02-30",
            "duration_minutes": "47",
        }
        codes = {issue.issue_code for issue in validate_record(row, 1)}
        self.assertIn("INVALID_ISO_DATE", codes)


if __name__ == "__main__":
    unittest.main()

