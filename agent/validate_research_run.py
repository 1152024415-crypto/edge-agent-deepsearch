#!/usr/bin/env python3
"""Validate a child-agent research run JSON file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import research_run


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate a research run before publishing.")
    parser.add_argument("path", help="Path to research_runs/<run>.json")
    parser.add_argument("--today", help="Override current date as YYYY-MM-DD for tests/replays")
    args = parser.parse_args(argv)

    try:
        payload = research_run.load_and_validate(args.path, today=args.today)
    except research_run.ValidationError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
