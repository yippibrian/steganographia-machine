from __future__ import annotations
from dataclasses import dataclass
from .models import EmittedStream, ExecutionResult, Text, UnitSequence

@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    actual: str
    expected: str
    execution: ExecutionResult


def result_text(execution: ExecutionResult) -> str:
    value = execution.value
    if isinstance(value, (Text, EmittedStream)):
        return value.value
    if isinstance(value, UnitSequence):
        return "".join(value.units)
    raise TypeError(f"unsupported result value: {type(value).__name__}")


def verify(execution: ExecutionResult, expected: str) -> VerificationResult:
    actual = result_text(execution)
    return VerificationResult(actual == expected, actual, expected, execution)
