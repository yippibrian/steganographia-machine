from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Schedule(Protocol):
    @property
    def mask(self) -> tuple[int, ...]: ...
    def selected(self, index: int) -> bool: ...
    def cycle_position(self, index: int) -> int: ...


@dataclass(frozen=True)
class MaskSchedule:
    values: tuple[int, ...]
    phase: int = 0

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("mask must contain at least one value")
        if any(value not in (0, 1) for value in self.values):
            raise ValueError("mask values must be 0 or 1")
        if self.phase < 0:
            raise ValueError("phase must be nonnegative")

    @property
    def mask(self) -> tuple[int, ...]:
        return self.values

    def cycle_position(self, index: int) -> int:
        return (index + self.phase) % len(self.values)

    def selected(self, index: int) -> bool:
        return bool(self.values[self.cycle_position(index)])
