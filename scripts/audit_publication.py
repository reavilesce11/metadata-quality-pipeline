"""Fail when a public repository contains common private-data indicators."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".csv",
    ".html",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".sql",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
FORBIDDEN_FILENAMES = {
    ".env",
    "configuracion.json",
    "credentials.json",
    "secrets.json",
}
PATTERNS = {
    "OpenAI-style secret": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{16,}\b"),
    "GitHub token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{16,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Windows user path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\", re.IGNORECASE),
    "private trading workspace": re.compile(r"[A-Za-z]:\\IA_TRADING_ORO\\", re.IGNORECASE),
    # The optional quote before the separator matters: without it the pattern
    # misses JSON, which is exactly how a leaked key usually looks.
    "credential assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|password|passwd|secret|token)['\"]?\s*[:=]\s*['\"][^'\"]+['\"]"
    ),
}


def publication_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode("utf-8") for item in completed.stdout.split(b"\0") if item]


def audit(paths: list[Path], root: Path = ROOT) -> list[str]:
    findings: list[str] = []
    for path in paths:
        relative = path.relative_to(root)
        if path.name.lower() in FORBIDDEN_FILENAMES:
            findings.append(f"forbidden filename: {relative}")
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{label}: {relative}")
    return findings


def main() -> int:
    findings = audit(publication_files())
    if findings:
        print("PUBLICATION AUDIT FAILED")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("PUBLICATION AUDIT PASSED")
    print("No tracked file matched the repository's private-data indicators.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
