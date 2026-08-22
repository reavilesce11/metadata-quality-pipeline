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


if __name__ == "__main__":
    unittest.main()

