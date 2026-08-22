# Metadata Quality Pipeline

A reproducible Python and SQL portfolio project that turns messy, synthetic episode metadata into accepted records, rejected records, and a human-review queue.

This project is inspired by the general problem of metadata quality. It does **not** contain Reelgood data, company code, screenshots, private rules, or confidential workflows.

## The business problem

Entertainment metadata often arrives with:

- inconsistent capitalization and whitespace;
- missing or invalid season and episode numbers;
- duplicate provider records;
- dates in invalid formats;
- implausible duration values;
- titles that do not match the canonical catalog.

Blind automation is dangerous. This pipeline automates clear cases and sends ambiguous cases to a review queue with an explicit reason.

## What the pipeline does

1. Loads a canonical episode catalog and an incoming provider feed.
2. Normalizes text without destroying the original values.
3. Validates required fields, numbers, dates, and duration.
4. Matches records by normalized series title, season number, and episode number.
5. Detects duplicate incoming episode keys.
6. Assigns one status:
   - `ACCEPTED`: valid and matched;
   - `REVIEW`: usable but ambiguous, incomplete, duplicated, or unmatched;
   - `REJECTED`: structurally invalid.
7. Writes clean CSV outputs, a JSON summary, and a SQLite audit database.
8. Runs a SQL quality report over the results.

## Quick start

From PowerShell:

```powershell
python -m pip install -e .
metadata-quality
python -m unittest discover -s tests -v
```

Or without installation:

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m metadata_quality.cli
python -m unittest discover -s tests -v
```

Generated files appear under `output/`:

- `processed_records.csv`
- `review_queue.csv`
- `quality_issues.csv`
- `quality_summary.json`
- `quality_dashboard.html`
- `metadata_quality.sqlite3`
- `quality_report.txt`

## Data lineage

The original provider values stay in `raw_records`. Normalized and matched values live in `processed_records`. Every warning or error has a stable code in `quality_issues`. This separation makes it possible to answer: what arrived, what changed, why it changed, and what still needs a person.

## Repository structure

```text
data/                  synthetic input files
sql/                   reusable quality report
src/metadata_quality/  pipeline source code
tests/                 automated tests
output/                generated artifacts, not committed
```

## Skills demonstrated

Python · CSV ingestion · normalization · deterministic matching · data-quality rules · exception handling · SQLite · SQL reporting · auditability · automated testing

## Honest scope

This is a portfolio implementation, not a copy of an employer's system. It demonstrates how Renato thinks about data quality and how he is developing from manual data operations toward reproducible data validation and automation.
