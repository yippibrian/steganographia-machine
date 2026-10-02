from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .errors import DefinitionError
from .engine.spec import pipeline_from_dict
from .engine.models import Text
from .historical.modes import compile_historical_mode
from .trace import render_trace
from .verifier import result_text


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Execute a v0.9 direct pipeline or historical mode method"
    )
    p.add_argument("method", type=Path)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--input", type=Path)
    p.add_argument("--expected")
    p.add_argument("--execution-json", help="case-specific execution parameters as a JSON object")
    p.add_argument("--trace", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    try:
        data = yaml.safe_load(args.method.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise DefinitionError("method file must contain a mapping")
        execution_parameters = (
            json.loads(args.execution_json) if args.execution_json else {}
        )
        if not isinstance(execution_parameters, dict):
            raise DefinitionError("--execution-json must decode to an object")

        has_pipeline = "pipeline" in data
        has_mode = "mode" in data
        if has_pipeline == has_mode:
            raise DefinitionError("method must define exactly one of pipeline or mode")
        if has_pipeline:
            pipeline = pipeline_from_dict({"pipeline": data["pipeline"]})
        else:
            pipeline = compile_historical_mode(
                data["mode"], execution_parameters
            ).pipeline

        source_text = (
            args.text
            if args.text is not None
            else args.input.read_text(encoding="utf-8")
        )
        execution = pipeline.execute(Text(source_text))
        output = result_text(execution)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
        DefinitionError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    matched = None if args.expected is None else output == args.expected
    if args.json:
        print(
            json.dumps(
                {"output": output, "matched": matched},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(output)
        if args.trace:
            print(render_trace(execution), file=sys.stderr)
        if matched is not None:
            print(
                "verification: PASS" if matched else "verification: FAIL",
                file=sys.stderr,
            )
    return 1 if matched is False else 0


if __name__ == "__main__":
    raise SystemExit(main())
