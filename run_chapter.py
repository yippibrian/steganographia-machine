#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from steg.compiler import compile_case
from steg.corpus import load_chapter
from steg.trace import render_trace
from steg.verifier import result_text


def _run_case(
    chapter,
    case_id: str,
    method_id: str | None,
    input_artifact: str | None,
    trace: bool,
) -> str:
    compiled = compile_case(
        chapter,
        case_id,
        method_id=method_id,
        input_artifact_id=input_artifact,
    )
    execution = compiled.execute()
    actual = result_text(execution)
    case = compiled.case

    if trace:
        print(render_trace(execution), file=sys.stderr)

    if not compiled.configured:
        status = "UNVERIFIED"
        expected = None
    elif case.expected_artifact:
        expected = chapter.artifacts[case.expected_artifact].path.read_text(
            encoding="utf-8"
        ).rstrip("\r\n")
        status = "PASS" if actual == expected else "FAIL"
    else:
        expected = None
        status = "UNVERIFIED"

    print(f"{status:<10} {case.id}")
    print(f"  method: {compiled.method.method.id}")
    print(f"  input:  {compiled.input_artifact_id}")
    print(f"  output: {actual}")
    if case.reading_artifact:
        reading = chapter.artifacts[case.reading_artifact].path.read_text(encoding="utf-8").rstrip("\r\n")
        print(f"  reading: {reading}")
    if status == "FAIL":
        print(f"  expected: {expected}")
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run methods and cases from a Book I chapter package"
    )
    parser.add_argument("chapter")
    parser.add_argument("--list-methods", action="store_true")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--list-artifacts", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--case")
    parser.add_argument("--method")
    parser.add_argument("--input-artifact")
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args(argv)

    chapter = load_chapter(ROOT / "corpus" / "book1" / args.chapter)

    if args.list_methods:
        for method in chapter.methods.values():
            print(method.id)
            print(f"  title: {method.title}")
        return 0

    if args.list_cases:
        for case in chapter.cases.values():
            print(case.id)
            print(f"  method: {case.method_id}")
            print(f"  status: {case.status}")
            print(f"  title:  {case.title}")
        return 0

    if args.list_artifacts:
        for artifact in chapter.artifacts.values():
            print(artifact.id)
            print(f"  role: {artifact.role}")
            print(f"  path: {artifact.path}")
        return 0

    if args.validate_only:
        print(f"PASS: {chapter.id}")
        return 0

    if args.input_artifact and not args.case:
        parser.error("--input-artifact requires --case")

    if args.case:
        statuses = [
            _run_case(
                chapter,
                args.case,
                args.method,
                args.input_artifact,
                args.trace,
            )
        ]
    else:
        selected = [
            case.id
            for case in chapter.cases.values()
            if args.method is None or case.method_id == args.method
        ]
        if not selected:
            parser.error("no cases match the requested method")
        statuses = [
            _run_case(chapter, case_id, None, None, args.trace)
            for case_id in selected
        ]

    parts = [
        f"{statuses.count(status)} {status.lower()}"
        for status in ("PASS", "FAIL", "UNVERIFIED")
        if statuses.count(status)
    ]
    print("\nSummary: " + ", ".join(parts))
    return 1 if "FAIL" in statuses else 0


if __name__ == "__main__":
    raise SystemExit(main())
