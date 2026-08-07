#!/usr/bin/env python3
"""Publish a validated research run to the display server."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib import request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import research_run
from research_collection import load_collection_manifest, validate_recorded_candidate_artifacts


def endpoint(server_url: str) -> str:
    return server_url.rstrip("/") + "/api/research-runs"


def publish_payload(
    server_url: str,
    payload: dict,
    token: str | None = None,
    timeout: int = 10,
    today=None,
) -> dict:
    normalized = research_run.validate_payload(
        payload,
        today=today,
        skip_network=True,
        require_collection_manifest=True,
    )
    validate_recorded_candidate_artifacts(normalized["collection_manifest"])
    if not token:
        raise research_run.ValidationError("publisher token is required")
    body = json.dumps(normalized, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(endpoint(server_url), data=body, headers=headers, method="POST")
    with request.urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode("utf-8")
    return json.loads(data) if data else {}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate and publish research run results.")
    parser.add_argument("path", help="Path to research_runs/<run>.json")
    parser.add_argument("--server", required=True, help="Server base URL, e.g. http://127.0.0.1:8000")
    parser.add_argument("--token", help="Bearer token; defaults to EDGE_PUBLISH_TOKEN")
    parser.add_argument("--today", help="Override current date as YYYY-MM-DD for tests/replays")
    parser.add_argument("--manifest", help="Collection manifest path; defaults to collection-manifest.json beside the run")
    parser.add_argument(
        "--allow-incomplete-coverage",
        action="store_true",
        help="Reserved for compatibility; server publishing rejects this bypass.",
    )
    args = parser.parse_args(argv)

    try:
        if args.allow_incomplete_coverage:
            raise ValueError(
                "publishing cannot bypass collection coverage; the flag is limited to local historical validation"
            )
        manifest = None
        manifest_path = Path(args.manifest) if args.manifest else Path(args.path).parent / "collection-manifest.json"
        manifest = load_collection_manifest(manifest_path, today=args.today)
        validate_recorded_candidate_artifacts(manifest)
        raw_payload = research_run.load_run_file(args.path)
        raw_payload["collection_manifest"] = manifest
        payload = research_run.validate_payload(raw_payload, today=args.today)
        result = publish_payload(
            args.server,
            payload,
            token=args.token or os.environ.get("EDGE_PUBLISH_TOKEN"),
            today=args.today,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    # Record this run's paper ids so the next validate can flag re-dumped papers.
    research_run.write_last_run_ids(payload["run_id"], [p["id"] for p in payload["papers"]])

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
