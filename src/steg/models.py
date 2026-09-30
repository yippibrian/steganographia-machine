from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union


@dataclass(frozen=True)
class Text:
    value: str


@dataclass(frozen=True)
class SourceSpan:
    """Coordinates in the input artifact before extraction loses geometry."""

    start: int
    end: int
    line: int
    column: int
    end_line: int
    end_column: int


@dataclass(frozen=True)
class UnitSequence:
    units: tuple[str, ...]
    unit_type: str
    spans: tuple[SourceSpan, ...] = ()

    def __post_init__(self) -> None:
        if self.spans and len(self.spans) != len(self.units):
            raise ValueError("spans must be empty or aligned one-to-one with units")


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
    classification: str = "significant"
    schedule_state: dict[str, Any] = field(default_factory=dict)
    source_span: SourceSpan | None = None


@dataclass(frozen=True)
class ProjectionDecision:
    index: int
    unit: str
    projected: str
    source_span: SourceSpan | None = None


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
