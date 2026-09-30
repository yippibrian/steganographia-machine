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


@dataclass(frozen=True)
class BoundaryResetSchedule:
    """Alternating blocks whose cycle can reset at supplied output boundaries.

    Boundaries are expressed as 1-based counts of selected/significant units.
    They are explicit inputs: this class does not infer hidden-word boundaries
    from an expected plaintext.
    """

    idle_run: int
    significant_run: int
    boundary_after_selected: tuple[int, ...]
    starts_with: str = "idle"
    reset_to_cycle_position: int = 0

    def __post_init__(self) -> None:
        base = AlternatingBlockSchedule(
            self.idle_run, self.significant_run, self.starts_with
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 1
            for value in self.boundary_after_selected
        ):
            raise ValueError("boundary_after_selected values must be positive integers")
        if tuple(sorted(set(self.boundary_after_selected))) != self.boundary_after_selected:
            raise ValueError("boundary_after_selected must be sorted and unique")
        if (
            isinstance(self.reset_to_cycle_position, bool)
            or not isinstance(self.reset_to_cycle_position, int)
            or not 0 <= self.reset_to_cycle_position < len(base.mask)
        ):
            raise ValueError("reset_to_cycle_position must address the base cycle")

    @property
    def mask(self) -> tuple[int, ...]:
        return AlternatingBlockSchedule(
            self.idle_run, self.significant_run, self.starts_with
        ).mask

    def _state_at(self, index: int) -> tuple[int, bool, int, bool]:
        if index < 0:
            raise ValueError("index must be nonnegative")
        position = 0
        selected_count = 0
        boundary_set = set(self.boundary_after_selected)
        for current in range(index + 1):
            selected = bool(self.mask[position])
            boundary_fired = False
            if selected:
                selected_count += 1
            if current == index:
                boundary_fired = selected and selected_count in boundary_set
                return position, selected, selected_count, boundary_fired
            position = (position + 1) % len(self.mask)
            if selected and selected_count in boundary_set:
                position = self.reset_to_cycle_position
        raise AssertionError("unreachable")

    def cycle_position(self, index: int) -> int:
        return self._state_at(index)[0]

    def selected(self, index: int) -> bool:
        return self._state_at(index)[1]

    def decision(self, index: int) -> ScheduleDecision:
        position, selected, selected_count, boundary_fired = self._state_at(index)
        return ScheduleDecision(
            selected,
            position,
            "significant" if selected else "idle",
            {
                "family": "boundary_reset_blocks",
                "starts_with": self.starts_with,
                "idle_run": self.idle_run,
                "significant_run": self.significant_run,
                "selected_count": selected_count,
                "boundary_after_selected": self.boundary_after_selected,
                "boundary_fired": boundary_fired,
                "reset_to_cycle_position": self.reset_to_cycle_position,
            },
        )
