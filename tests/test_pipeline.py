from __future__ import annotations

import csv
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from metadata_quality.pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_pipeline_routes_records_and_persists_audit_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)
            result = run_pipeline(
                self.root / "data" / "canonical_episodes.csv",
                self.root / "data" / "incoming_episodes.csv",
                output,
                self.root / "sql" / "quality_report.sql",
            )

            self.assertEqual(result.total_records, 10)
            self.assertEqual(result.accepted_records, 3)
            self.assertEqual(result.review_records, 5)
            self.assertEqual(result.rejected_records, 2)
            self.assertEqual(result.total_issues, 8)

            summary = json.loads((output / "quality_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status_counts"], {"ACCEPTED": 3, "REJECTED": 2, "REVIEW": 5})
            dashboard = (output / "quality_dashboard.html").read_text(encoding="utf-8")
            self.assertIn("Metadata Quality Report", dashboard)
            self.assertIn("Human review · 50%", dashboard)

            with (output / "review_queue.csv").open(encoding="utf-8", newline="") as handle:
                review_rows = list(csv.DictReader(handle))
            self.assertEqual(len(review_rows), 7)

            with closing(sqlite3.connect(output / "metadata_quality.sqlite3")) as connection:
                raw_count = connection.execute("SELECT COUNT(*) FROM raw_records").fetchone()[0]
                issue_count = connection.execute("SELECT COUNT(*) FROM quality_issues").fetchone()[0]
            self.assertEqual(raw_count, 10)
            self.assertEqual(issue_count, 8)


if __name__ == "__main__":
    unittest.main()
