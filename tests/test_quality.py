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
                "INVALID_DURATION_FORMAT",
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

    def test_unreadable_and_out_of_range_durations_get_different_codes(self) -> None:
        """A reviewer must not be told that 45000 and "not_known" failed alike."""
        base = {
            "provider_record_id": "P300",
            "series_title": "Deep Orbit",
            "season_number": "1",
            "episode_number": "1",
            "episode_title": "First Light",
            "air_date": "2026-01-05",
        }
        unreadable = {issue.issue_code for issue in validate_record({**base, "duration_minutes": "not_known"}, 1)}
        out_of_range = {issue.issue_code for issue in validate_record({**base, "duration_minutes": "45000"}, 1)}
        self.assertEqual(unreadable, {"INVALID_DURATION_FORMAT"})
        self.assertEqual(out_of_range, {"IMPLAUSIBLE_DURATION"})

    def test_duration_rejects_python_integer_shortcuts(self) -> None:
        """Duration must obey the same strict feed syntax as other integers."""
        base = {
            "provider_record_id": "P301",
            "series_title": "Deep Orbit",
            "season_number": "1",
            "episode_number": "1",
            "episode_title": "First Light",
            "air_date": "2026-01-05",
        }
        for value in ("1_0", "+3", "3.0", "٣"):
            with self.subTest(duration_minutes=value):
                codes = {
                    issue.issue_code
                    for issue in validate_record({**base, "duration_minutes": value}, 1)
                }
                self.assertEqual(codes, {"INVALID_DURATION_FORMAT"})

        # NFKC intentionally converts full-width display digits to ASCII.
        self.assertEqual(validate_record({**base, "duration_minutes": "３"}, 1), [])


if __name__ == "__main__":
    unittest.main()

