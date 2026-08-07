#!/usr/bin/env python3
"""Validate a child-agent research run JSON file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import research_run
from research_collection import (
    CollectionCoverageError,
    load_collection_manifest,
    validate_recorded_candidate_artifacts,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate a research run before publishing.")
    parser.add_argument("path", help="Path to research_runs/<run>.json")
    parser.add_argument("--today", help="Override current date as YYYY-MM-DD for tests/replays")
    parser.add_argument("--manifest", help="Collection manifest path; defaults to collection-manifest.json beside the run")
    parser.add_argument(
        "--allow-incomplete-coverage",
        action="store_true",
        help="Historical recovery only; never use for a normal weekly publish.",
    )
    args = parser.parse_args(argv)

    try:
        manifest = None
        if not args.allow_incomplete_coverage:
            manifest_path = Path(args.manifest) if args.manifest else Path(args.path).parent / "collection-manifest.json"
            manifest = load_collection_manifest(manifest_path, today=args.today)
            validate_recorded_candidate_artifacts(manifest)
        raw_payload = research_run.load_run_file(args.path)
        if manifest is not None:
            raw_payload["collection_manifest"] = manifest
        payload = research_run.validate_payload(raw_payload, today=args.today)
    except (research_run.ValidationError, CollectionCoverageError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
