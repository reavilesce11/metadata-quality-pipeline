"""Command-line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline


def _default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    root = _default_root()
    parser = argparse.ArgumentParser(description="Run the synthetic metadata quality pipeline.")
    parser.add_argument("--canonical", type=Path, default=root / "data" / "canonical_episodes.csv")
    parser.add_argument("--incoming", type=Path, default=root / "data" / "incoming_episodes.csv")
    parser.add_argument("--output", type=Path, default=root / "output")
    parser.add_argument("--sql-report", type=Path, default=root / "sql" / "quality_report.sql")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run_pipeline(args.canonical, args.incoming, args.output, args.sql_report)
    print("Metadata Quality Pipeline")
    print(f"Total:    {result.total_records}")
    print(f"Accepted: {result.accepted_records}")
    print(f"Review:   {result.review_records}")
    print(f"Rejected: {result.rejected_records}")
    print(f"Issues:   {result.total_issues}")
    print(f"Output:   {result.output_directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

