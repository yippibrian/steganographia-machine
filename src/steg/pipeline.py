from __future__ import annotations
from dataclasses import dataclass
from .models import ExecutionResult, PipelineValue, TraceEvent
from .stages import Stage

@dataclass(frozen=True)
class Pipeline:
    stages: tuple[Stage, ...]

    def execute(self, value: PipelineValue) -> ExecutionResult:
        trace: list[TraceEvent] = []
        current = value
        for stage in self.stages:
            current, event = stage.execute(current)
            trace.append(event)
        return ExecutionResult(current, tuple(trace))
