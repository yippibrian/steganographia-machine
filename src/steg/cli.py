from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any
import yaml
from .loader import DefinitionError, pipeline_from_dict
from .models import Text
from .trace import render_trace
from .verifier import result_text


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Execute a v0.8 declarative method")
    p.add_argument("method", type=Path)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--input", type=Path)
    p.add_argument("--expected")
    p.add_argument("--trace", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        data = yaml.safe_load(args.method.read_text(encoding="utf-8"))
        pipeline = pipeline_from_dict({"pipeline": data["pipeline"]})
        source_text = args.text if args.text is not None else args.input.read_text(encoding="utf-8")
        execution = pipeline.execute(Text(source_text))
        output = result_text(execution)
    except (OSError, UnicodeError, KeyError, TypeError, ValueError, DefinitionError) as exc:
        print(f"error: {exc}", file=sys.stderr); return 2
    matched = None if args.expected is None else output == args.expected
    if args.json:
        print(json.dumps({"output": output, "matched": matched}, ensure_ascii=False, indent=2))
    else:
        print(output)
        if args.trace: print(render_trace(execution), file=sys.stderr)
        if matched is not None: print("verification: PASS" if matched else "verification: FAIL", file=sys.stderr)
    return 1 if matched is False else 0
