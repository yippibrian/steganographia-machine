from __future__ import annotations

import re


WORD_RE = re.compile(r"\b[^\W\d_]+(?:['’-][^\W\d_]+)*\b", re.UNICODE)


def word_matches(text: str):
    """Return matches using the project's single canonical word definition."""
    return tuple(WORD_RE.finditer(text))


def words(text: str) -> tuple[str, ...]:
    return tuple(match.group(0) for match in word_matches(text))
