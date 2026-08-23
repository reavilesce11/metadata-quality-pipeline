"""Explicit quality rules and stable issue codes."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date

from .normalization import normalize_text, parse_positive_integer


# The rule this project publishes is YYYY-MM-DD, so the shape is checked before
# the calendar is. Since Python 3.11, date.fromisoformat() also accepts the
# basic form 20260131 and ISO week dates such as 2026-W05-1, which would let a
# feed drift away from the documented contract without a single warning.
_ISO_CALENDAR_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


@dataclass(frozen=True)
class QualityIssue:
    provider_record_id: str
    row_number: int
    severity: str
    issue_code: str
    field_name: str
    observed_value: str
    message: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _issue(
    record_id: str,
    row_number: int,
    severity: str,
    issue_code: str,
    field_name: str,
    observed_value: object,
    message: str,
) -> QualityIssue:
    return QualityIssue(
        provider_record_id=record_id,
        row_number=row_number,
        severity=severity,
        issue_code=issue_code,
        field_name=field_name,
        observed_value=normalize_text(observed_value),
        message=message,
    )


def validate_record(row: dict[str, str], row_number: int) -> list[QualityIssue]:
    """Validate one incoming record without changing it."""

    record_id = normalize_text(row.get("provider_record_id")) or f"ROW_{row_number}"
    issues: list[QualityIssue] = []

    for field_name in ("provider_record_id", "series_title"):
        if not normalize_text(row.get(field_name)):
            issues.append(
                _issue(
                    record_id,
                    row_number,
                    "ERROR",
                    "REQUIRED_FIELD_MISSING",
                    field_name,
                    row.get(field_name),
                    f"{field_name} is required.",
                )
            )

    for field_name in ("season_number", "episode_number"):
        if parse_positive_integer(row.get(field_name)) is None:
            issues.append(
                _issue(
                    record_id,
                    row_number,
                    "ERROR",
                    "INVALID_POSITIVE_INTEGER",
                    field_name,
                    row.get(field_name),
                    f"{field_name} must be a positive integer.",
                )
            )

    air_date = normalize_text(row.get("air_date"))
    if air_date:
        valid_date = bool(_ISO_CALENDAR_DATE.fullmatch(air_date))
        if valid_date:
            try:
                date.fromisoformat(air_date)
            except ValueError:
                valid_date = False
        if not valid_date:
            issues.append(
                _issue(
                    record_id,
                    row_number,
                    "ERROR",
                    "INVALID_ISO_DATE",
                    "air_date",
                    air_date,
                    "air_date must use the ISO format YYYY-MM-DD.",
                )
            )

    duration = normalize_text(row.get("duration_minutes"))
    if duration:
        try:
            duration_number = int(duration)
        except ValueError:
            duration_number = 0
        if not 1 <= duration_number <= 300:
            issues.append(
                _issue(
                    record_id,
                    row_number,
                    "WARNING",
                    "IMPLAUSIBLE_DURATION",
                    "duration_minutes",
                    duration,
                    "duration_minutes should be between 1 and 300.",
                )
            )

    if not normalize_text(row.get("episode_title")):
        issues.append(
            _issue(
                record_id,
                row_number,
                "WARNING",
                "EPISODE_TITLE_MISSING",
                "episode_title",
                row.get("episode_title"),
                "The record can be matched, but its episode title needs review.",
            )
        )

    return issues

