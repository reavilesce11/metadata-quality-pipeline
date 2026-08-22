"""End-to-end metadata quality pipeline."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .dashboard import write_dashboard
from .normalization import normalize_key, normalize_text, parse_positive_integer
from .quality import QualityIssue, validate_record


@dataclass(frozen=True)
class PipelineResult:
    total_records: int
    accepted_records: int
    review_records: int
    rejected_records: int
    total_issues: int
    output_directory: Path
    database_path: Path


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _catalog_key(row: dict[str, str]) -> tuple[str, int, int] | None:
    series_key = normalize_key(row.get("series_title"))
    season = parse_positive_integer(row.get("season_number"))
    episode = parse_positive_integer(row.get("episode_number"))
    if not series_key or season is None or episode is None:
        return None
    return series_key, season, episode


def _write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _status_for(issues: list[QualityIssue]) -> str:
    if any(issue.severity == "ERROR" for issue in issues):
        return "REJECTED"
    if issues:
        return "REVIEW"
    return "ACCEPTED"


def _build_database(
    database_path: Path,
    raw_rows: list[dict[str, str]],
    processed_rows: list[dict[str, object]],
    issues: list[QualityIssue],
) -> None:
    if database_path.exists():
        database_path.unlink()
    with closing(sqlite3.connect(database_path)) as connection:
        connection.executescript(
            """
            CREATE TABLE raw_records (
                provider_record_id TEXT,
                source_row INTEGER PRIMARY KEY,
                raw_json TEXT NOT NULL
            );

            CREATE TABLE processed_records (
                provider_record_id TEXT NOT NULL,
                source_row INTEGER PRIMARY KEY,
                canonical_id TEXT,
                series_title_original TEXT,
                series_title_normalized TEXT,
                season_number INTEGER,
                episode_number INTEGER,
                episode_title TEXT,
                air_date TEXT,
                duration_minutes TEXT,
                status TEXT NOT NULL
            );

            CREATE TABLE quality_issues (
                provider_record_id TEXT NOT NULL,
                source_row INTEGER NOT NULL,
                severity TEXT NOT NULL,
                issue_code TEXT NOT NULL,
                field_name TEXT NOT NULL,
                observed_value TEXT,
                message TEXT NOT NULL
            );

            CREATE INDEX idx_processed_status ON processed_records(status);
            CREATE INDEX idx_processed_provider_id ON processed_records(provider_record_id);
            CREATE INDEX idx_issues_code ON quality_issues(issue_code);
            """
        )
        connection.executemany(
            "INSERT INTO raw_records VALUES (?, ?, ?)",
            [
                (
                    normalize_text(row.get("provider_record_id")),
                    row_number,
                    json.dumps(row, ensure_ascii=False, sort_keys=True),
                )
                for row_number, row in enumerate(raw_rows, start=2)
            ],
        )
        connection.executemany(
            """
            INSERT INTO processed_records VALUES (
                :provider_record_id, :source_row, :canonical_id,
                :series_title_original, :series_title_normalized,
                :season_number, :episode_number, :episode_title,
                :air_date, :duration_minutes, :status
            )
            """,
            processed_rows,
        )
        connection.executemany(
            """
            INSERT INTO quality_issues VALUES (
                :provider_record_id, :row_number, :severity, :issue_code,
                :field_name, :observed_value, :message
            )
            """,
            [issue.as_dict() for issue in issues],
        )
        connection.commit()


def _write_sql_report(database_path: Path, sql_path: Path, report_path: Path) -> None:
    statements = [part.strip() for part in sql_path.read_text(encoding="utf-8").split(";") if part.strip()]
    lines: list[str] = []
    with closing(sqlite3.connect(database_path)) as connection:
        for index, statement in enumerate(statements, start=1):
            cursor = connection.execute(statement)
            columns = [item[0] for item in cursor.description]
            rows = cursor.fetchall()
            lines.append(f"REPORT {index}")
            lines.append(" | ".join(columns))
            lines.extend(" | ".join(str(value) for value in row) for row in rows)
            lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def run_pipeline(
    canonical_path: Path,
    incoming_path: Path,
    output_directory: Path,
    sql_report_path: Path,
) -> PipelineResult:
    """Run validation, matching, review routing, persistence, and reporting."""

    canonical_rows = _read_csv(canonical_path)
    incoming_rows = _read_csv(incoming_path)
    output_directory.mkdir(parents=True, exist_ok=True)

    catalog = {
        key: row
        for row in canonical_rows
        if (key := _catalog_key(row)) is not None
    }
    seen_keys: dict[tuple[str, int, int], str] = {}
    seen_record_ids: dict[str, int] = {}
    all_issues: list[QualityIssue] = []
    processed_rows: list[dict[str, object]] = []

    for row_number, row in enumerate(incoming_rows, start=2):
        record_id = normalize_text(row.get("provider_record_id")) or f"ROW_{row_number}"
        record_issues = validate_record(row, row_number)
        key = _catalog_key(row)
        canonical = catalog.get(key) if key is not None else None

        if record_id in seen_record_ids:
            record_issues.append(
                QualityIssue(
                    provider_record_id=record_id,
                    row_number=row_number,
                    severity="WARNING",
                    issue_code="DUPLICATE_PROVIDER_RECORD_ID",
                    field_name="provider_record_id",
                    observed_value=record_id,
                    message=f"Same provider_record_id as source row {seen_record_ids[record_id]}.",
                )
            )
        else:
            seen_record_ids[record_id] = row_number

        if key is not None and key in seen_keys:
            record_issues.append(
                QualityIssue(
                    provider_record_id=record_id,
                    row_number=row_number,
                    severity="WARNING",
                    issue_code="DUPLICATE_INCOMING_KEY",
                    field_name="series_title,season_number,episode_number",
                    observed_value="|".join(str(item) for item in key),
                    message=f"Same normalized episode key as {seen_keys[key]}.",
                )
            )
        elif key is not None:
            seen_keys[key] = record_id

        if key is not None and canonical is None:
            record_issues.append(
                QualityIssue(
                    provider_record_id=record_id,
                    row_number=row_number,
                    severity="WARNING",
                    issue_code="NO_CANONICAL_MATCH",
                    field_name="series_title,season_number,episode_number",
                    observed_value="|".join(str(item) for item in key),
                    message="No canonical episode matches the normalized key.",
                )
            )

        status = _status_for(record_issues)
        processed_rows.append(
            {
                "provider_record_id": record_id,
                "source_row": row_number,
                "canonical_id": normalize_text(canonical.get("canonical_id")) if canonical else "",
                "series_title_original": normalize_text(row.get("series_title")),
                "series_title_normalized": normalize_key(row.get("series_title")),
                "season_number": parse_positive_integer(row.get("season_number")) or "",
                "episode_number": parse_positive_integer(row.get("episode_number")) or "",
                "episode_title": normalize_text(row.get("episode_title")),
                "air_date": normalize_text(row.get("air_date")),
                "duration_minutes": normalize_text(row.get("duration_minutes")),
                "status": status,
            }
        )
        all_issues.extend(record_issues)

    processed_fields = [
        "provider_record_id",
        "source_row",
        "canonical_id",
        "series_title_original",
        "series_title_normalized",
        "season_number",
        "episode_number",
        "episode_title",
        "air_date",
        "duration_minutes",
        "status",
    ]
    issue_fields = [
        "provider_record_id",
        "row_number",
        "severity",
        "issue_code",
        "field_name",
        "observed_value",
        "message",
    ]
    _write_csv(output_directory / "processed_records.csv", processed_rows, processed_fields)
    _write_csv(
        output_directory / "accepted_records.csv",
        [row for row in processed_rows if row["status"] == "ACCEPTED"],
        processed_fields,
    )
    _write_csv(
        output_directory / "review_queue.csv",
        [row for row in processed_rows if row["status"] == "REVIEW"],
        processed_fields,
    )
    _write_csv(
        output_directory / "rejected_records.csv",
        [row for row in processed_rows if row["status"] == "REJECTED"],
        processed_fields,
    )
    _write_csv(
        output_directory / "quality_issues.csv",
        [issue.as_dict() for issue in all_issues],
        issue_fields,
    )

    status_counts = Counter(str(row["status"]) for row in processed_rows)
    issue_counts = Counter(issue.issue_code for issue in all_issues)
    summary = {
        "total_records": len(processed_rows),
        "status_counts": dict(sorted(status_counts.items())),
        "issue_counts": dict(sorted(issue_counts.items())),
        "total_issues": len(all_issues),
    }
    (output_directory / "quality_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_dashboard(
        output_directory / "quality_dashboard.html",
        len(processed_rows),
        status_counts,
        all_issues,
    )

    database_path = output_directory / "metadata_quality.sqlite3"
    _build_database(database_path, incoming_rows, processed_rows, all_issues)
    _write_sql_report(database_path, sql_report_path, output_directory / "quality_report.txt")

    return PipelineResult(
        total_records=len(processed_rows),
        accepted_records=status_counts["ACCEPTED"],
        review_records=status_counts["REVIEW"],
        rejected_records=status_counts["REJECTED"],
        total_issues=len(all_issues),
        output_directory=output_directory,
        database_path=database_path,
    )
