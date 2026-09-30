from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml
from .models import ArtifactRef, ChapterDefinition, CipherCase, EvidenceRef, MethodDefinition
from ..loader import DefinitionError, pipeline_from_dict
from ..modes import compile_historical_mode

class ChapterDefinitionError(ValueError):
    pass

ALLOWED_CASE_STATUSES = {"verified", "unverified", "falsified", "blocked"}
REQUIRED_PROVENANCE_PATHS = (
    "protocol.address.direction",
    "protocol.authority.principal",
    "protocol.sign.required_on_carrier",
    "protocol.sender.invocation_artifact",
    "protocol.recipient.invocation_artifact",
    "protocol.carrier.semantics",
)


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ChapterDefinitionError(f"{path}: expected a mapping")
    return data


def _add_unique(target: dict[str, Any], key: str, value: Any, context: str) -> None:
    if key in target:
        raise ChapterDefinitionError(f"duplicate {context} id: {key}")
    target[key] = value


def _tuple_map(value: Any, context: str) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict):
        raise ChapterDefinitionError(f"{context}: expected a mapping")
    result = {}
    for path, refs in value.items():
        refs = [refs] if isinstance(refs, str) else refs
        if not isinstance(refs, list) or not all(isinstance(ref, str) for ref in refs):
            raise ChapterDefinitionError(f"{context}.{path}: expected evidence ids")
        result[str(path)] = tuple(refs)
    return result


def load_chapter(path: str | Path) -> ChapterDefinition:
    root = Path(path)
    data = _read_yaml(root / "chapter.yaml")
    required = {"id", "book", "chapter", "title", "principal", "protocol", "provenance", "artifacts", "evidence", "methods", "cases"}
    missing = sorted(required - set(data))
    if missing:
        raise ChapterDefinitionError(f"{root/'chapter.yaml'}: missing {', '.join(missing)}")

    artifacts: dict[str, ArtifactRef] = {}
    for item in data["artifacts"]:
        artifact = ArtifactRef(item["id"], item["role"], root / item["path"], item.get("language"), item.get("transcription"))
        _add_unique(artifacts, artifact.id, artifact, "artifact")

    evidence: dict[str, EvidenceRef] = {}
    for item in data["evidence"]:
        ref = EvidenceRef(item["id"], item["source"], item["relation"], item.get("quotation"), item.get("confidence", "explicit"))
        _add_unique(evidence, ref.id, ref, "evidence")

    methods: dict[str, MethodDefinition] = {}
    for rel in data["methods"]:
        item = _read_yaml(root / rel)
        pipeline = item.get("pipeline")
        mode = item.get("mode")
        if (pipeline is None) == (mode is None):
            raise ChapterDefinitionError(f"{rel}: define exactly one of pipeline or mode")
        if pipeline is not None and not isinstance(pipeline, list):
            raise ChapterDefinitionError(f"{rel}: pipeline must be a list")
        if mode is not None and not isinstance(mode, dict):
            raise ChapterDefinitionError(f"{rel}: mode must be a mapping")
        method = MethodDefinition(
            item["id"],
            item["title"],
            tuple(pipeline) if pipeline is not None else None,
            mode,
            tuple(item.get("evidence", [])),
            tuple(item.get("notes", [])),
        )
        _add_unique(methods, method.id, method, "method")

    cases: dict[str, CipherCase] = {}
    for rel in data["cases"]:
        item = _read_yaml(root / rel)
        case = CipherCase(item["id"], item["title"], item["method"], item["input_artifact"], item.get("expected_artifact"), item.get("reading_artifact"), item["status"], tuple(item.get("evidence", [])), tuple(item.get("notes", [])))
        _add_unique(cases, case.id, case, "case")

    chapter = ChapterDefinition(data["id"], int(data["book"]), int(data["chapter"]), data["title"], data["principal"], root, data["protocol"], _tuple_map(data["provenance"], "provenance"), artifacts, evidence, methods, cases)
    validate_chapter(chapter)
    return chapter


def validate_chapter(chapter: ChapterDefinition) -> None:
    errors: list[str] = []
    for artifact in chapter.artifacts.values():
        if not artifact.path.is_file():
            errors.append(f"artifact {artifact.id} does not exist: {artifact.path}")
    for method in chapter.methods.values():
        for ref in method.evidence:
            if ref not in chapter.evidence:
                errors.append(f"method {method.id}: unknown evidence {ref}")
        try:
            if method.pipeline is not None:
                pipeline_from_dict({"pipeline": list(method.pipeline)})
            else:
                compile_historical_mode(method.mode or {})
        except DefinitionError as exc:
            errors.append(f"method {method.id}: {exc}")
    for case in chapter.cases.values():
        if case.status not in ALLOWED_CASE_STATUSES:
            errors.append(f"case {case.id}: unknown status {case.status}")
        if case.method_id not in chapter.methods:
            errors.append(f"case {case.id}: unknown method {case.method_id}")
        if case.input_artifact not in chapter.artifacts:
            errors.append(f"case {case.id}: unknown input artifact {case.input_artifact}")
        if case.expected_artifact and case.expected_artifact not in chapter.artifacts:
            errors.append(f"case {case.id}: unknown expected artifact {case.expected_artifact}")
        if case.reading_artifact and case.reading_artifact not in chapter.artifacts:
            errors.append(f"case {case.id}: unknown reading artifact {case.reading_artifact}")
        if case.status == "verified" and not case.expected_artifact:
            errors.append(f"case {case.id}: verified case requires expected_artifact")
        for ref in case.evidence:
            if ref not in chapter.evidence:
                errors.append(f"case {case.id}: unknown evidence {ref}")
    for path in REQUIRED_PROVENANCE_PATHS:
        if path not in chapter.provenance:
            errors.append(f"provenance missing {path}")
    for path, refs in chapter.provenance.items():
        for ref in refs:
            if ref not in chapter.evidence:
                errors.append(f"provenance {path}: unknown evidence {ref}")
            elif chapter.evidence[ref].relation != path:
                errors.append(f"provenance {path}: evidence {ref} relation mismatch")
    if errors:
        raise ChapterDefinitionError("; ".join(errors))
