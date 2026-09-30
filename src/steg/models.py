from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union


@dataclass(frozen=True)
class Text:
    value: str


@dataclass(frozen=True)
class UnitSequence:
    units: tuple[str, ...]
    unit_type: str


@dataclass(frozen=True)
class EmittedStream:
    value: str


PipelineValue = Union[Text, UnitSequence, EmittedStream]


@dataclass(frozen=True)
class SelectionDecision:
    index: int
    unit: str
    cycle_position: int
    selected: bool


@dataclass(frozen=True)
class ProjectionDecision:
    index: int
    unit: str
    projected: str


@dataclass(frozen=True)
class TraceEvent:
    stage: str
    input_type: str
    output_type: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionResult:
    value: PipelineValue
    trace: tuple[TraceEvent, ...]
