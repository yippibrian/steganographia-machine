from __future__ import annotations
from dataclasses import dataclass
from ..corpus.models import ChapterDefinition, CipherCase, MethodDefinition
from ..engine.spec import pipeline_from_dict
from ..engine.models import ExecutionResult, Text
from ..historical.modes import CompiledMode, compile_historical_mode
from ..engine.pipeline import Pipeline

@dataclass(frozen=True)
class CompiledMethod:
    chapter: ChapterDefinition
    method: MethodDefinition
    pipeline: Pipeline
    historical_mode: CompiledMode | None = None

    def execute(self, source: str) -> ExecutionResult:
        return self.pipeline.execute(Text(source))

@dataclass(frozen=True)
class CompiledCase:
    chapter: ChapterDefinition
    case: CipherCase
    method: CompiledMethod
    input_artifact_id: str
    configured: bool = True

    def execute(self) -> ExecutionResult:
        artifact = self.chapter.artifacts[self.input_artifact_id]
        return self.method.execute(artifact.path.read_text(encoding="utf-8"))


def compile_method(
    chapter: ChapterDefinition,
    method_id: str,
    *,
    execution_parameters: dict | None = None,
) -> CompiledMethod:
    try:
        method = chapter.methods[method_id]
    except KeyError as exc:
        raise KeyError(f"unknown method {method_id!r}; available: {', '.join(sorted(chapter.methods))}") from exc
    if method.pipeline is not None:
        return CompiledMethod(chapter, method, pipeline_from_dict({"pipeline": list(method.pipeline)}))
    compiled_mode = compile_historical_mode(
        method.mode or {}, execution_parameters or {}
    )
    return CompiledMethod(chapter, method, compiled_mode.pipeline, compiled_mode)


def compile_case(chapter: ChapterDefinition, case_id: str, *, method_id: str | None = None, input_artifact_id: str | None = None) -> CompiledCase:
    try:
        case = chapter.cases[case_id]
    except KeyError as exc:
        raise KeyError(f"unknown case {case_id!r}; available: {', '.join(sorted(chapter.cases))}") from exc
    chosen_method = method_id or case.method_id
    chosen_input = input_artifact_id or case.input_artifact
    if chosen_input not in chapter.artifacts:
        raise KeyError(f"unknown artifact {chosen_input!r}; available: {', '.join(sorted(chapter.artifacts))}")
    configured = chosen_method == case.method_id and chosen_input == case.input_artifact
    return CompiledCase(
        chapter,
        case,
        compile_method(
            chapter,
            chosen_method,
            execution_parameters=dict(case.execution),
        ),
        chosen_input,
        configured,
    )
