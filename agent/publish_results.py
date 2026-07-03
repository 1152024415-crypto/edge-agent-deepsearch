#!/usr/bin/env python3
"""Publish a validated research run to the display server."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib import request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import research_run


def endpoint(server_url: str) -> str:
    return server_url.rstrip("/") + "/api/research-runs"


def publish_payload(server_url: str, payload: dict, token: str | None = None, timeout: int = 10) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
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
    parser.add_argument("--token", help="Optional bearer token")
    parser.add_argument("--today", help="Override current date as YYYY-MM-DD for tests/replays")
    args = parser.parse_args(argv)

    try:
        payload = research_run.load_and_validate(args.path, today=args.today)
        result = publish_payload(args.server, payload, token=args.token)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    # Record this run's paper ids so the next validate can flag re-dumped papers.
    research_run.write_last_run_ids(payload["run_id"], [p["id"] for p in payload["papers"]])

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
