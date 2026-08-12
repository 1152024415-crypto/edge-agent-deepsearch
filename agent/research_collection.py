#!/usr/bin/env python3
"""Shared collection window and source-coverage contract for weekly research."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse


class CollectionCoverageError(ValueError):
    """Raised when a weekly source-coverage manifest is incomplete or stale."""


REQUIRED_ARXIV_SWEEPS = frozenset({
    "cs.AI-broad",
    "cs.LG-broad",
    "cs.CL-broad",
    "cs.RO-broad",
    "cs.AR-broad",
    "cs.DC-broad",
    "cs.ET-broad",
    "cs.SY-broad",
    "cs.NE-broad",
    "recent-updates",
})

REQUIRED_GITHUB_PROJECTS = frozenset({
    "ggml-org/llama.cpp",
    "pytorch/executorch",
    "mlc-ai/mlc-llm",
    "microsoft/onnxruntime",
    "alibaba/MNN",
    "Tencent/ncnn",
    "google-ai-edge/mediapipe",
    "google-ai-edge/litert",
    "apple/coremltools",
    "ml-explore/mlx",
    "openvinotoolkit/openvino",
    "PowerInfer/PowerInfer",
    "HKUDS/nanobot",
    "microsoft/Orchard",
    "YINGLINGH/limioryn",
})

REQUIRED_VENDOR_SOURCES = frozenset({
    "Apple", "Samsung", "Huawei", "Qualcomm", "MediaTek", "Xiaomi", "OPPO", "vivo", "Honor",
    "Google", "Microsoft", "OpenAI", "Anthropic", "Meta", "NVIDIA", "Mistral", "ModelBest", "Qwen",
    "StepFun", "DeepSeek", "Moonshot", "Zhipu", "MiniMax", "Baichuan",
})


def normalize_github_project(value: str) -> str:
    """Return a case-insensitive ``owner/repo`` key from a repo name or GitHub URL."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    if "://" in raw:
        parsed = urlparse(raw)
        if (parsed.hostname or "").lower() not in {"github.com", "www.github.com"}:
            return ""
        parts = [part for part in parsed.path.split("/") if part]
    else:
        parts = [part for part in raw.split("/") if part]
    if len(parts) < 2:
        return ""
    owner = parts[0].strip()
    repo = parts[1].strip()
    if repo.lower().endswith(".git"):
        repo = repo[:-4]
    return f"{owner}/{repo}".lower() if owner and repo else ""


def is_required_github_project(value: str) -> bool:
    normalized = normalize_github_project(value)
    return normalized in {project.lower() for project in REQUIRED_GITHUB_PROJECTS}


def parse_collection_date(value: str | date | None = None) -> date:
    if value is None:
        return date.today()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CollectionCoverageError(f"invalid collection date: {value!r}") from exc


def collection_window(today: str | date | None = None, days: int = 7) -> tuple[date, date, list[date]]:
    """Return an inclusive window containing exactly ``days`` calendar dates."""
    if days < 1:
        raise CollectionCoverageError("collection window days must be positive")
    end = parse_collection_date(today)
    start = end - timedelta(days=days - 1)
    dates = [start + timedelta(days=offset) for offset in range(days)]
    return start, end, dates


def _require_source(sources: dict, name: str) -> dict:
    value = sources.get(name)
    if not isinstance(value, dict):
        raise CollectionCoverageError(f"collection source {name!r} is missing")
    if value.get("status") != "complete":
        raise CollectionCoverageError(f"collection source {name!r} is not complete")
    count = value.get("candidate_count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise CollectionCoverageError(
            f"collection source {name!r} candidate_count must be a non-negative integer"
        )
    artifact_path = value.get("artifact_path")
    if not isinstance(artifact_path, str) or not artifact_path.strip():
        raise CollectionCoverageError(
            f"collection source {name!r} artifact_path is required; run attest_candidates.py"
        )
    artifact_sha256 = value.get("artifact_sha256")
    if not isinstance(artifact_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", artifact_sha256):
        raise CollectionCoverageError(
            f"collection source {name!r} artifact_sha256 must be a 64-character lowercase hex digest"
        )
    candidate_refs = value.get("candidate_refs")
    if (
        not isinstance(candidate_refs, list)
        or len(candidate_refs) != count
        or len(set(candidate_refs)) != len(candidate_refs)
        or any(not isinstance(ref, str) or not re.fullmatch(r"[0-9a-f]{64}", ref) for ref in candidate_refs)
    ):
        raise CollectionCoverageError(
            f"collection source {name!r} candidate_refs must contain one unique SHA-256 per candidate"
        )
    identity_refs = value.get("candidate_identity_refs")
    if (
        not isinstance(identity_refs, list)
        or len(identity_refs) != count
        or len(set(identity_refs)) != len(identity_refs)
        or any(not isinstance(ref, str) or not re.fullmatch(r"[0-9a-f]{64}", ref) for ref in identity_refs)
    ):
        raise CollectionCoverageError(
            f"collection source {name!r} candidate_identity_refs must contain one stable identity per candidate"
        )
    lineage = value.get("candidate_lineage")
    if (
        not isinstance(lineage, dict)
        or set(lineage) != set(candidate_refs)
        or set(lineage.values()) != set(identity_refs)
    ):
        raise CollectionCoverageError(
            f"collection source {name!r} candidate_lineage must bind every record ref to its identity"
        )
    return value


def _missing(required: frozenset[str], actual) -> list[str]:
    return sorted(required - {str(value) for value in (actual or [])})


def validate_collection_manifest(manifest: dict, today: str | date | None = None) -> dict:
    if not isinstance(manifest, dict):
        raise CollectionCoverageError("collection manifest must be a JSON object")
    start, end, expected_dates = collection_window(today)
    if manifest.get("window_start") != start.isoformat() or manifest.get("window_end") != end.isoformat():
        raise CollectionCoverageError(
            f"collection window must be {start.isoformat()}..{end.isoformat()} for this run"
        )
    sources = manifest.get("sources")
    if not isinstance(sources, dict):
        raise CollectionCoverageError("collection manifest sources must be an object")

    arxiv = _require_source(sources, "arxiv")
    missing_arxiv = _missing(REQUIRED_ARXIV_SWEEPS, arxiv.get("queries_completed"))
    if missing_arxiv:
        raise CollectionCoverageError(f"arxiv broad sweeps missing: {', '.join(missing_arxiv)}")
    pages_fetched = arxiv.get("pages_fetched")
    if (
        not isinstance(pages_fetched, int)
        or isinstance(pages_fetched, bool)
        or pages_fetched < len(REQUIRED_ARXIV_SWEEPS)
    ):
        raise CollectionCoverageError(
            f"arxiv pages_fetched must be at least {len(REQUIRED_ARXIV_SWEEPS)} "
            "so every required broad sweep has a response page"
        )

    huggingface = _require_source(sources, "huggingface")
    expected_hf = {day.isoformat() for day in expected_dates}
    actual_hf = {str(day) for day in (huggingface.get("dates_checked") or [])}
    if actual_hf != expected_hf:
        missing_days = sorted(expected_hf - actual_hf)
        extra_days = sorted(actual_hf - expected_hf)
        raise CollectionCoverageError(
            f"huggingface dates_checked does not cover the exact window; "
            f"missing={missing_days}, extra={extra_days}"
        )

    github = _require_source(sources, "github")
    missing_projects = _missing(REQUIRED_GITHUB_PROJECTS, github.get("release_projects_checked"))
    if missing_projects:
        raise CollectionCoverageError(f"github release projects missing: {', '.join(missing_projects)}")
    if github.get("trending_checked") is not True:
        raise CollectionCoverageError("github trending and release scans are separate; trending_checked must be true")

    vendors = _require_source(sources, "vendors")
    missing_vendors = _missing(REQUIRED_VENDOR_SOURCES, vendors.get("vendors_checked"))
    if missing_vendors:
        raise CollectionCoverageError(f"vendor sources missing: {', '.join(missing_vendors)}")
    checks = vendors.get("vendor_checks")
    if not isinstance(checks, dict):
        raise CollectionCoverageError("vendor_checks must contain per-vendor source evidence")
    for vendor in sorted(REQUIRED_VENDOR_SOURCES):
        check = checks.get(vendor)
        if not isinstance(check, dict):
            raise CollectionCoverageError(f"vendor check missing: {vendor}")
        if check.get("status") not in {"found", "no_match"}:
            raise CollectionCoverageError(
                f"vendor {vendor} has no completed check evidence: status={check.get('status')!r}"
            )
        succeeded = check.get("sources_succeeded")
        if not isinstance(succeeded, list) or not succeeded:
            raise CollectionCoverageError(f"vendor {vendor} has no successfully checked official source")

    return manifest


def validate_candidate_counts(manifest: dict, actual_counts: dict[str, int]) -> None:
    """Bind self-reported coverage to the candidate arrays used by the assembler."""
    sources = manifest.get("sources") if isinstance(manifest, dict) else None
    if not isinstance(sources, dict):
        raise CollectionCoverageError("collection manifest sources must be an object")
    for source, actual in actual_counts.items():
        coverage = sources.get(source)
        if not isinstance(coverage, dict):
            raise CollectionCoverageError(f"collection source {source!r} is missing")
        expected = coverage.get("candidate_count")
        if expected != actual:
            raise CollectionCoverageError(
                f"{source} candidate_count mismatch: manifest={expected!r}, artifact={actual}"
            )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def candidate_record_ref(candidate: dict) -> str:
    if not isinstance(candidate, dict):
        raise CollectionCoverageError("each candidate artifact row must be a JSON object")
    canonical = json.dumps(
        candidate,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def candidate_output_identity(source: str, candidate: dict) -> tuple[str, str, str]:
    """Return the immutable title/URL/date identity a converter must preserve."""
    title = str(candidate.get("title") or "").strip()
    if source == "arxiv":
        aid = re.sub(r"v\d+$", "", str(candidate.get("id") or "")).strip()
        paper_url = f"https://arxiv.org/abs/{aid}" if aid else ""
    elif source == "huggingface":
        paper_url = str(candidate.get("paper_url") or "").strip()
        match = re.search(r"arxiv\.org/abs/([^v\s]+)", paper_url)
        if match:
            paper_url = f"https://huggingface.co/papers/{match.group(1)}"
    elif source == "github":
        repo = str(candidate.get("repo") or "").strip()
        tag = str(candidate.get("tag") or "").strip()
        title = title or f"{repo} {tag}".strip()
        paper_url = str(candidate.get("release_url") or f"https://github.com/{repo}").strip()
    elif source == "vendors":
        paper_url = str(candidate.get("url") or "").strip()
    else:
        raise CollectionCoverageError(f"unknown candidate source: {source!r}")
    source_date = str(candidate.get("date") or candidate.get("published") or "").strip()[:10]
    return title, paper_url, source_date


def candidate_identity_ref(source: str, title: str, paper_url: str, source_date: str) -> str:
    canonical = json.dumps(
        {
            "source": source,
            "title": title.strip(),
            "paper_url": paper_url.strip(),
            "date": source_date.strip(),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def candidate_artifact_attestation(path: str | Path, source: str) -> dict:
    artifact_path = Path(path).resolve()
    if not artifact_path.is_file():
        raise CollectionCoverageError(f"candidate artifact missing: {artifact_path}")
    try:
        candidates = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CollectionCoverageError(f"invalid candidate artifact {artifact_path}: {exc}") from exc
    if not isinstance(candidates, list):
        raise CollectionCoverageError(f"candidate artifact must be a JSON list: {artifact_path}")
    candidate_refs = [candidate_record_ref(candidate) for candidate in candidates]
    if len(set(candidate_refs)) != len(candidate_refs):
        raise CollectionCoverageError(f"candidate artifact contains duplicate rows: {artifact_path}")
    identity_refs = [
        candidate_identity_ref(source, *candidate_output_identity(source, candidate))
        for candidate in candidates
    ]
    if len(set(identity_refs)) != len(identity_refs):
        raise CollectionCoverageError(
            f"candidate artifact contains duplicate output identities for {source}: {artifact_path}"
        )
    return {
        "artifact_path": str(artifact_path),
        "artifact_sha256": _sha256(artifact_path),
        "candidate_count": len(candidates),
        "candidate_refs": candidate_refs,
        "candidate_identity_refs": identity_refs,
        "candidate_lineage": dict(zip(candidate_refs, identity_refs)),
    }


def validate_candidate_artifacts(manifest: dict, artifacts: dict[str, str | Path]) -> None:
    """Verify candidate paths, hashes, and row counts before run assembly."""
    sources = manifest.get("sources") if isinstance(manifest, dict) else None
    if not isinstance(sources, dict):
        raise CollectionCoverageError("collection manifest sources must be an object")
    actual_counts: dict[str, int] = {}
    for source, path in artifacts.items():
        coverage = sources.get(source)
        if not isinstance(coverage, dict):
            raise CollectionCoverageError(f"collection source {source!r} is missing")
        actual = candidate_artifact_attestation(path, source)
        recorded_path = coverage.get("artifact_path")
        if not recorded_path or Path(recorded_path).resolve() != Path(actual["artifact_path"]):
            raise CollectionCoverageError(
                f"{source} artifact_path mismatch: manifest={recorded_path!r}, "
                f"artifact={actual['artifact_path']!r}"
            )
        if coverage.get("artifact_sha256") != actual["artifact_sha256"]:
            raise CollectionCoverageError(f"{source} artifact_sha256 does not match the candidate file")
        if coverage.get("candidate_refs") != actual["candidate_refs"]:
            raise CollectionCoverageError(f"{source} candidate_refs do not match the candidate file")
        if coverage.get("candidate_identity_refs") != actual["candidate_identity_refs"]:
            raise CollectionCoverageError(
                f"{source} candidate_identity_refs do not match the candidate file"
            )
        if coverage.get("candidate_lineage") != actual["candidate_lineage"]:
            raise CollectionCoverageError(f"{source} candidate_lineage does not match the candidate file")
        actual_counts[source] = actual["candidate_count"]
    validate_candidate_counts(manifest, actual_counts)


def validate_recorded_candidate_artifacts(manifest: dict) -> None:
    """Recheck every artifact recorded in a complete manifest on the producer machine."""
    sources = manifest.get("sources") if isinstance(manifest, dict) else None
    if not isinstance(sources, dict):
        raise CollectionCoverageError("collection manifest sources must be an object")
    artifacts = {
        source: coverage.get("artifact_path")
        for source, coverage in sources.items()
        if source in {"arxiv", "huggingface", "github", "vendors"}
        and isinstance(coverage, dict)
    }
    if set(artifacts) != {"arxiv", "huggingface", "github", "vendors"}:
        raise CollectionCoverageError("all four candidate artifact paths must be recorded")
    validate_candidate_artifacts(manifest, artifacts)


def validate_run_candidate_lineage(papers: list[dict], manifest: dict) -> None:
    """Ensure every published item points to an exact row in an attested candidate file."""
    sources = manifest.get("sources") if isinstance(manifest, dict) else None
    if not isinstance(sources, dict):
        raise CollectionCoverageError("collection manifest sources must be an object")
    allowed_sources = {"arxiv", "huggingface", "github", "vendors"}
    used_refs: set[tuple[str, str]] = set()
    for paper in papers:
        paper_id = str(paper.get("id") or "<unknown>")
        source = paper.get("candidate_source")
        ref = paper.get("candidate_ref")
        if source not in allowed_sources:
            raise CollectionCoverageError(f"{paper_id}: candidate_source is missing or invalid")
        coverage = sources.get(source)
        refs = coverage.get("candidate_refs") if isinstance(coverage, dict) else None
        if not isinstance(refs, list) or ref not in refs:
            raise CollectionCoverageError(
                f"{paper_id}: candidate_ref is not present in the attested {source} artifact"
            )
        lineage_key = (source, ref)
        if lineage_key in used_refs:
            raise CollectionCoverageError(f"{paper_id}: candidate_ref is reused by multiple run items")
        used_refs.add(lineage_key)
        if source == "github":
            if paper.get("source_tier") != "开源大项目":
                raise CollectionCoverageError(
                    f"{paper_id}: GitHub candidates must use source_tier=开源大项目"
                )
            if not is_required_github_project(str(paper.get("paper_url") or "")):
                raise CollectionCoverageError(
                    f"{paper_id}: GitHub candidate is not in the big-project whitelist"
                )
        identity_ref = candidate_identity_ref(
            source,
            str(paper.get("title") or ""),
            str(paper.get("paper_url") or ""),
            str(paper.get("date") or ""),
        )
        lineage = coverage.get("candidate_lineage")
        if not isinstance(lineage, dict) or lineage.get(ref) != identity_ref:
            raise CollectionCoverageError(
                f"{paper_id}: title/paper_url/date identity does not match the attested candidate"
            )


def load_collection_manifest(path: str | Path, today: str | date | None = None) -> dict:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise CollectionCoverageError(f"collection manifest not found: {manifest_path}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CollectionCoverageError(f"invalid collection manifest {manifest_path}: {exc}") from exc
    return validate_collection_manifest(payload, today=today)


def update_source_coverage(
    path: str | Path,
    source: str,
    coverage: dict,
    today: str | date | None = None,
) -> dict:
    """Merge one collector's auditable result into the weekly manifest."""
    start, end, _ = collection_window(today)
    manifest_path = Path(path)
    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "sources": {},
    }
    if manifest_path.exists():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = {}
        if (
            previous.get("window_start") == start.isoformat()
            and previous.get("window_end") == end.isoformat()
            and isinstance(previous.get("sources"), dict)
        ):
            manifest["sources"] = previous["sources"]
    current = manifest["sources"].get(source)
    merged = dict(current) if isinstance(current, dict) else {}
    merged.update(coverage)
    manifest["sources"][source] = merged
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
