from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import (
    ArtifactRef,
    ChapterDefinition,
    CipherCase,
    ClaimRef,
    EvidenceRef,
    MethodDefinition,
)
from ..loader import DefinitionError, pipeline_from_dict
from ..modes import compile_historical_mode


class ChapterDefinitionError(ValueError):
    pass


ALLOWED_CASE_STATUSES = {"verified", "unverified", "falsified", "blocked"}
ALLOWED_CLAIM_STATUSES = {
    "documented",
    "reconstructed",
    "hypothesis",
    "unresolved",
    "contradicted",
}
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


def _string_tuple(value: Any, context: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ChapterDefinitionError(f"{context}: expected a list of strings")
    return tuple(value)


def _contained_path(root: Path, relative: Any, context: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ChapterDefinitionError(f"{context}: path must be a non-empty string")
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ChapterDefinitionError(f"{context}: path escapes chapter root: {relative}") from exc
    return candidate


def load_chapter(path: str | Path) -> ChapterDefinition:
    root = Path(path)
    data = _read_yaml(root / "chapter.yaml")
    required = {
        "id", "book", "chapter", "title", "principal", "protocol", "provenance",
        "artifacts", "evidence", "methods", "cases",
    }
    missing = sorted(required - set(data))
    if missing:
        raise ChapterDefinitionError(
            f"{root/'chapter.yaml'}: missing {', '.join(missing)}"
        )

    artifacts: dict[str, ArtifactRef] = {}
    for item in data["artifacts"]:
        artifact = ArtifactRef(
            id=item["id"],
            role=item["role"],
            path=_contained_path(root, item["path"], f"artifact {item['id']}"),
            language=item.get("language"),
            transcription=item.get("transcription"),
            witness=item.get("witness"),
            locator=item.get("locator"),
            derived_from=item.get("derived_from"),
            transformations=_string_tuple(
                item.get("transformations"), f"artifact {item['id']}.transformations"
            ),
            evidence=_string_tuple(
                item.get("evidence"), f"artifact {item['id']}.evidence"
            ),
        )
        _add_unique(artifacts, artifact.id, artifact, "artifact")

    evidence: dict[str, EvidenceRef] = {}
    for item in data["evidence"]:
        ref = EvidenceRef(
            item["id"],
            item["source"],
            item["relation"],
            item.get("quotation"),
            item.get("confidence", "explicit"),
        )
        _add_unique(evidence, ref.id, ref, "evidence")

    claims: dict[str, ClaimRef] = {}
    for item in data.get("claims", []):
        claim = ClaimRef(
            id=item["id"],
            proposition=item["proposition"],
            status=item["status"],
            evidence=_string_tuple(item.get("evidence"), f"claim {item['id']}.evidence"),
            scope=item.get("scope"),
            contradicts=_string_tuple(
                item.get("contradicts"), f"claim {item['id']}.contradicts"
            ),
            notes=_string_tuple(item.get("notes"), f"claim {item['id']}.notes"),
        )
        _add_unique(claims, claim.id, claim, "claim")

    methods: dict[str, MethodDefinition] = {}
    for rel in data["methods"]:
        item = _read_yaml(root / rel)
        pipeline = item.get("pipeline")
        mode = item.get("mode")
        if (pipeline is None) == (mode is None):
            raise ChapterDefinitionError(
                f"{rel}: define exactly one of pipeline or mode"
            )
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
        case = CipherCase(
            item["id"],
            item["title"],
            item["method"],
            item["input_artifact"],
            item.get("expected_artifact"),
            item.get("reading_artifact"),
            item["status"],
            tuple(item.get("evidence", [])),
            tuple(item.get("notes", [])),
            item.get("execution", {}),
        )
        if not isinstance(case.execution, dict):
            raise ChapterDefinitionError(f"{rel}: execution must be a mapping")
        _add_unique(cases, case.id, case, "case")

    chapter = ChapterDefinition(
        data["id"],
        int(data["book"]),
        int(data["chapter"]),
        data["title"],
        data["principal"],
        root,
        data["protocol"],
        _tuple_map(data["provenance"], "provenance"),
        artifacts,
        evidence,
        methods,
        cases,
        claims,
    )
    validate_chapter(chapter)
    return chapter


def _protocol_path_exists(protocol: Any, dotted_path: str) -> bool:
    parts = dotted_path.split(".")
    if not parts or parts[0] != "protocol":
        return False
    current = protocol
    for part in parts[1:]:
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True


def validate_chapter(chapter: ChapterDefinition) -> None:
    errors: list[str] = []

    for artifact in chapter.artifacts.values():
        if not artifact.path.is_file():
            errors.append(f"artifact {artifact.id} does not exist: {artifact.path}")
        if artifact.derived_from:
            if artifact.derived_from == artifact.id:
                errors.append(f"artifact {artifact.id}: cannot derive from itself")
            elif artifact.derived_from not in chapter.artifacts:
                errors.append(
                    f"artifact {artifact.id}: unknown parent artifact {artifact.derived_from}"
                )
        for ref in artifact.evidence:
            if ref not in chapter.evidence:
                errors.append(f"artifact {artifact.id}: unknown evidence {ref}")

    for claim in chapter.claims.values():
        if claim.status not in ALLOWED_CLAIM_STATUSES:
            errors.append(f"claim {claim.id}: unknown status {claim.status}")
        for ref in claim.evidence:
            if ref not in chapter.evidence:
                errors.append(f"claim {claim.id}: unknown evidence {ref}")
        for other in claim.contradicts:
            if other not in chapter.claims:
                errors.append(f"claim {claim.id}: unknown contradicted claim {other}")
            elif other == claim.id:
                errors.append(f"claim {claim.id}: cannot contradict itself")

    for method in chapter.methods.values():
        for ref in method.evidence:
            if ref not in chapter.evidence:
                errors.append(f"method {method.id}: unknown evidence {ref}")
        try:
            if method.pipeline is not None:
                pipeline_from_dict({"pipeline": list(method.pipeline)})
            else:
                compile_historical_mode(method.mode or {}, allow_unbound_modifiers=True)
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
            errors.append(
                f"case {case.id}: unknown expected artifact {case.expected_artifact}"
            )
        if case.reading_artifact and case.reading_artifact not in chapter.artifacts:
            errors.append(
                f"case {case.id}: unknown reading artifact {case.reading_artifact}"
            )
        if case.status == "verified" and not case.expected_artifact:
            errors.append(f"case {case.id}: verified case requires expected_artifact")
        for ref in case.evidence:
            if ref not in chapter.evidence:
                errors.append(f"case {case.id}: unknown evidence {ref}")

    for path in REQUIRED_PROVENANCE_PATHS:
        if path not in chapter.provenance:
            errors.append(f"provenance missing {path}")

    for path, refs in chapter.provenance.items():
        if not _protocol_path_exists(chapter.protocol, path):
            errors.append(f"provenance path does not exist in protocol: {path}")
        if not refs:
            errors.append(f"provenance {path}: requires at least one evidence reference")
        for ref in refs:
            if ref not in chapter.evidence:
                errors.append(f"provenance {path}: unknown evidence {ref}")
            elif chapter.evidence[ref].relation != path:
                errors.append(f"provenance {path}: evidence {ref} relation mismatch")

    for section in ("sender", "recipient"):
        value = chapter.protocol.get(section, {}).get("invocation_artifact")
        if value is not None and value not in chapter.artifacts:
            errors.append(
                f"protocol.{section}.invocation_artifact: unknown artifact {value}"
            )
    sign_artifact = chapter.protocol.get("sign", {}).get("artifact")
    if sign_artifact is not None and sign_artifact not in chapter.artifacts:
        errors.append(f"protocol.sign.artifact: unknown artifact {sign_artifact}")

    if errors:
        raise ChapterDefinitionError("; ".join(errors))
