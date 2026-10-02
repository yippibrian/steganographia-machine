from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSpan:
    """Coordinates in the input artifact before extraction loses geometry."""

    start: int
    end: int
    line: int
    column: int
    end_line: int
    end_column: int


def source_span(text: str, start: int, end: int) -> SourceSpan:
    """Map character offsets to one-based line/column coordinates."""
    line = text.count("\n", 0, start) + 1
    last_newline = text.rfind("\n", 0, start)
    column = start - last_newline
    end_line = text.count("\n", 0, end) + 1
    end_last_newline = text.rfind("\n", 0, end)
    end_column = end - end_last_newline
    return SourceSpan(start, end, line, column, end_line, end_column)
