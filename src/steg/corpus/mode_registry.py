from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ModeRegistryEntry:
    name: str
    chapter: int
    mode: int
    family: str | None
    historical_notation: str | None
    implementation_status: str
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ModeRegistry:
    expected_catalogue_size: int
    source: str
    entries: dict[str, ModeRegistryEntry]


ALLOWED_IMPLEMENTATION_STATUSES = {
    "verified",
    "executable",
    "represented",
    "requires_stateful_rules",
    "unclassified",
}


def load_mode_registry(path: str | Path) -> ModeRegistry:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("mode registry must be a mapping")
    expected = data.get("expected_catalogue_size")
    if isinstance(expected, bool) or not isinstance(expected, int) or expected < 1:
        raise ValueError("expected_catalogue_size must be a positive integer")
    source = data.get("source")
    if not isinstance(source, str) or not source:
        raise ValueError("mode registry source must be a non-empty string")
    entries: dict[str, ModeRegistryEntry] = {}
    for item in data.get("modes", []):
        entry = ModeRegistryEntry(
            name=item["name"],
            chapter=int(item["chapter"]),
            mode=int(item["mode"]),
            family=item.get("family"),
            historical_notation=item.get("historical_notation"),
            implementation_status=item.get("implementation_status", "unclassified"),
            notes=tuple(item.get("notes", [])),
        )
        if entry.name in entries:
            raise ValueError(f"duplicate mode registry name: {entry.name}")
        if entry.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            raise ValueError(
                f"mode {entry.name}: unknown implementation status "
                f"{entry.implementation_status}"
            )
        if entry.historical_notation is not None and any(
            symbol not in {"o", "."} for symbol in entry.historical_notation
        ):
            raise ValueError(
                f"mode {entry.name}: historical_notation must contain only o and ."
            )
        entries[entry.name] = entry
    return ModeRegistry(expected, source, entries)
