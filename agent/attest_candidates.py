#!/usr/bin/env python3
"""Bind the four final candidate JSON files to the weekly coverage manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from research_collection import (
    CollectionCoverageError,
    candidate_artifact_attestation,
    load_collection_manifest,
    parse_collection_date,
    update_source_coverage,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS = {
    "arxiv": ROOT / ".superpowers" / "sdd" / "arxiv_candidates.json",
    "huggingface": ROOT / "research_runs" / "candidates-hf.json",
    "github": ROOT / "research_runs" / "candidates-github.json",
    "vendors": ROOT / "research_runs" / "candidates-vendor.json",
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Record exact candidate paths, counts, and SHA-256 hashes in the collection manifest."
    )
    parser.add_argument("--today", help="Override collection date as YYYY-MM-DD")
    parser.add_argument(
        "--manifest",
        default=str(ROOT / "research_runs" / "collection-manifest.json"),
    )
    args = parser.parse_args(argv)
    run_date = parse_collection_date(args.today)
    try:
        for source, path in DEFAULT_ARTIFACTS.items():
            update_source_coverage(
                args.manifest,
                source,
                candidate_artifact_attestation(path, source),
                today=run_date,
            )
        load_collection_manifest(args.manifest, today=run_date)
    except CollectionCoverageError as exc:
        print(f"[ATTEST] FAIL: {exc}")
        return 1
    print(f"[ATTEST] OK: bound {len(DEFAULT_ARTIFACTS)} candidate artifacts to {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
