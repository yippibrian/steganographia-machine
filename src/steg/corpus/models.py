from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

@dataclass(frozen=True)
class EvidenceRef:
    id: str
    source: str
    relation: str
    quotation: str | None = None
    confidence: str = "explicit"

@dataclass(frozen=True)
class ArtifactRef:
    id: str
    role: str
    path: Path
    language: str | None = None
    transcription: str | None = None

@dataclass(frozen=True)
class MethodDefinition:
    id: str
    title: str
    pipeline: tuple[Mapping[str, Any], ...]
    evidence: tuple[str, ...]
    notes: tuple[str, ...]

@dataclass(frozen=True)
class CipherCase:
    id: str
    title: str
    method_id: str
    input_artifact: str
    expected_artifact: str | None
    reading_artifact: str | None
    status: str
    evidence: tuple[str, ...]
    notes: tuple[str, ...]

@dataclass(frozen=True)
class ChapterDefinition:
    id: str
    book: int
    chapter: int
    title: str
    principal: str
    root: Path
    protocol: Mapping[str, Any]
    provenance: Mapping[str, tuple[str, ...]]
    artifacts: Mapping[str, ArtifactRef]
    evidence: Mapping[str, EvidenceRef]
    methods: Mapping[str, MethodDefinition]
    cases: Mapping[str, CipherCase]
