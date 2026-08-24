"""Small deterministic normalization helpers."""

from __future__ import annotations

import re
import unicodedata


_WHITESPACE = re.compile(r"\s+")

# Only plain ASCII digits count as a number here. Python's int() is far more
# permissive than a catalog feed should be: it reads "+3" as 3, "1_0" as 10 and
# Arabic-Indic digits as their Western value. A typed underscore silently
# becoming season 10 is exactly the kind of quiet corruption this pipeline
# exists to stop, so anything outside 0-9 goes to a person instead.
_ASCII_DIGITS = re.compile(r"[0-9]+")


def normalize_text(value: object) -> str:
    """Normalize Unicode and whitespace while preserving readable casing."""

    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKC", text)
    return _WHITESPACE.sub(" ", text).strip()


def normalize_key(value: object) -> str:
    """Create a comparison key that is insensitive to case and whitespace."""

    return normalize_text(value).casefold()


def parse_ascii_integer(value: object) -> int | None:
    """Return an ASCII integer or None when the syntax is invalid."""

    text = normalize_text(value)
    if not _ASCII_DIGITS.fullmatch(text):
        return None
    return int(text)


def parse_positive_integer(value: object) -> int | None:
    """Return a positive ASCII integer or None when the value is invalid."""

    number = parse_ascii_integer(value)
    if number is None:
        return None
    return number if number > 0 else None
