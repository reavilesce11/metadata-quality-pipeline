"""Small deterministic normalization helpers."""

from __future__ import annotations

import re
import unicodedata


_WHITESPACE = re.compile(r"\s+")


def normalize_text(value: object) -> str:
    """Normalize Unicode and whitespace while preserving readable casing."""

    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKC", text)
    return _WHITESPACE.sub(" ", text).strip()


def normalize_key(value: object) -> str:
    """Create a comparison key that is insensitive to case and whitespace."""

    return normalize_text(value).casefold()


def parse_positive_integer(value: object) -> int | None:
    """Return a positive integer or None when the value is invalid."""

    text = normalize_text(value)
    if not text:
        return None
    try:
        number = int(text)
    except ValueError:
        return None
    return number if number > 0 else None

