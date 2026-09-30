from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..errors import DefinitionError


@dataclass(frozen=True)
class BlockPattern:
    """Shared structural meaning of a simple idle/significant word cycle."""

    idle_run: int
    significant_run: int
    starts_with: str

    @classmethod
    def from_parameters(
        cls,
        parameters: Mapping[str, Any],
        mode_name: str,
    ) -> "BlockPattern":
        idle_run = _positive(parameters.get("idle_run"), "idle_run", mode_name)
        significant_run = _positive(
            parameters.get("significant_run"), "significant_run", mode_name
        )
        starts_with = parameters.get("starts_with", "idle")
        if starts_with not in {"idle", "significant"}:
            raise DefinitionError(
                f"mode {mode_name}: starts_with must be 'idle' or 'significant'"
            )
        return cls(idle_run, significant_run, starts_with)

    @property
    def classifications(self) -> tuple[str, ...]:
        idle = ("idle",) * self.idle_run
        significant = ("significant",) * self.significant_run
        return (
            idle + significant
            if self.starts_with == "idle"
            else significant + idle
        )

    @property
    def notation(self) -> str:
        return "".join(
            "o" if classification == "idle" else "."
            for classification in self.classifications
        )

    @property
    def schedule_spec(self) -> dict[str, Any]:
        return {
            "type": "alternating_blocks",
            "idle_run": self.idle_run,
            "significant_run": self.significant_run,
            "starts_with": self.starts_with,
        }


def _positive(value: Any, label: str, mode_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DefinitionError(
            f"mode {mode_name}: {label} must be a positive integer"
        )
    return value
