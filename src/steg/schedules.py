from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ScheduleDecision:
    selected: bool
    cycle_position: int
    classification: str
    state: dict[str, Any]


class Schedule(Protocol):
    @property
    def mask(self) -> tuple[int, ...]: ...

    def decision(self, index: int) -> ScheduleDecision: ...

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

    def decision(self, index: int) -> ScheduleDecision:
        position = self.cycle_position(index)
        selected = bool(self.values[position])
        return ScheduleDecision(
            selected,
            position,
            "significant" if selected else "idle",
            {"phase": self.phase, "family": "mask"},
        )


@dataclass(frozen=True)
class AlternatingBlockSchedule:
    """Semantic schedule for runs of idle and significant carrier units."""

    idle_run: int
    significant_run: int
    starts_with: str = "idle"

    def __post_init__(self) -> None:
        if isinstance(self.idle_run, bool) or not isinstance(self.idle_run, int) or self.idle_run < 1:
            raise ValueError("idle_run must be a positive integer")
        if isinstance(self.significant_run, bool) or not isinstance(self.significant_run, int) or self.significant_run < 1:
            raise ValueError("significant_run must be a positive integer")
        if self.starts_with not in {"idle", "significant"}:
            raise ValueError("starts_with must be 'idle' or 'significant'")

    @property
    def mask(self) -> tuple[int, ...]:
        idle = (0,) * self.idle_run
        significant = (1,) * self.significant_run
        return idle + significant if self.starts_with == "idle" else significant + idle

    def cycle_position(self, index: int) -> int:
        return index % len(self.mask)

    def selected(self, index: int) -> bool:
        return bool(self.mask[self.cycle_position(index)])

    def decision(self, index: int) -> ScheduleDecision:
        position = self.cycle_position(index)
        selected = self.selected(index)
        return ScheduleDecision(
            selected,
            position,
            "significant" if selected else "idle",
            {
                "family": "alternating_blocks",
                "starts_with": self.starts_with,
                "idle_run": self.idle_run,
                "significant_run": self.significant_run,
            },
        )
