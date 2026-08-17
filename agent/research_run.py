#!/usr/bin/env python3
"""Validation helpers for child-agent research run JSON files.

Schema (方案 B, 2 维评分 + 多标签 + source_tier):
- score = score_relevance(0-10) + score_contribution(0-10), 上限 20。
- source_tier: 官方动态 / 公司项目 / 学校顶会 / 开源大项目（facet，不打分）。
- tags: 1-6 个，必须取自 data/tags.yaml 词表。
- open_source: bool facet。
- edge_agent_scope: 主 Agent 原文核实后的设备范围；真正端侧 Agent 必须推荐。
- date: 必须落在当前日期过去 7 天（一周）窗口内；arXiv URL 会核对真实 submitted date。
"""

from __future__ import annotations

import json
import re
import socket
import sys
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

from research_collection import (
    CollectionCoverageError,
    collection_window,
    is_required_github_project,
    validate_collection_manifest,
    validate_run_candidate_lineage,
)


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PAPER_FIELDS = (
    "id",
    "title",
    "abstract",
    "effects",
    "mechanism",
    "paper_url",
    "date",
    "score",
    "score_reason",
    "source_tier",
    "tags",
    "open_source",
    "score_relevance",
    "score_contribution",
    "edge_agent_scope",
)

# 2 维评分: 字段名 -> 满分。score 必须等于 2 维之和。
SCORE_DIMENSIONS = (
    ("score_relevance", 10),
    ("score_contribution", 10),
)

ALLOWED_SOURCE_TIERS = {"官方动态", "开源大项目", "公司项目", "学校顶会", "学校预印本"}
OFFICIAL_TIER = "官方动态"
COMPANY_TIER = "公司项目"
OSS_TIER = "开源大项目"
ALLOWED_EDGE_AGENT_SCOPES = {"待核实", "手机", "PC", "其他端侧", "非端侧Agent"}
DIRECT_EDGE_AGENT_SCOPES = {"手机", "PC", "其他端侧"}
DIRECT_EDGE_AGENT_TAG = "方向:端侧agent"

# source_tier=官方动态 时 paper_url 必须命中以下官方域名。
OFFICIAL_SOURCE_DOMAINS = (
    "apple.com",
    "developer.apple.com",
    "machinelearning.apple.com",
    "google.com",
    "blog.google",
    "googleblog.com",
    "android-developers.googleblog.com",
    "ai.google.dev",
    "microsoft.com",
    "azure.microsoft.com",
    "techcommunity.microsoft.com",
    "openai.com",
    "anthropic.com",
    "meta.com",
    "ai.meta.com",
    "about.fb.com",
    "samsung.com",
    "research.samsung.com",
    "huawei.com",
    "qualcomm.com",
    "mediatek.com",
    "mi.com",
    "xiaomi.com",
    "oppo.com",
    "vivo.com",
    "vivo.com.cn",
    "honor.com",
    "alibabacloud.com",
    "qwenlm.github.io",
    "mistral.ai",
    "nvidia.com",
    "blogs.nvidia.com",
    "developer.nvidia.com",
    "deepseek.com",
    "api-docs.deepseek.com",
    "kimi.com",
    "moonshot.cn",
    "zhipuai.cn",
    "bigmodel.cn",
    "baichuan-ai.com",
    "modelbest.cn",
    "minimaxi.com",
    "stepfun.com",
    "minimax.io",
)

AFFILIATION_EVIDENCE_DOMAINS = (
    "openreview.net",
    "scholar.google.com",
    "arxiv.org",
    "aclanthology.org",
    "openaccess.thecvf.com",
    "proceedings.neurips.cc",
    "dl.acm.org",
    "ieeexplore.ieee.org",
    "link.springer.com",
    "sciencedirect.com",
    "orcid.org",
)

ARXIV_URL_RE = re.compile(
    r"^https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/([^/?#]+)", re.IGNORECASE
)
CJK_RE = re.compile(r"[\u3400-\u9fff]")
INTERNAL_PLACEHOLDER_RE = re.compile(
    r"auto[- ]?converted|待核实|待后续补|精修.{0,12}待补|votes\s*=|"
    r"自动初评|(?<!自)主\s*Agent|待复核",
    re.IGNORECASE,
)
MIN_CHINESE_CHARS = 8


class ValidationError(Exception):
    """Raised when a research run cannot be published."""


def load_run_file(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as fh:
        try:
            payload = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationError(f"{path}: top-level JSON must be an object")
    return payload


def parse_today(value: str | date | None = None) -> date:
    if value is None:
        return date.today()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError as exc:
        raise ValidationError(f"invalid --today value: {value!r}") from exc


def text_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def bool_value(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def require_reader_facing_chinese(value, field: str, paper_id: str) -> str:
    """Validate text shown directly to readers on the recommendation surface."""
    text = text_value(value)
    if len(CJK_RE.findall(text)) < MIN_CHINESE_CHARS:
        raise ValidationError(
            f"{paper_id}: {field} 必须是可直接阅读的中文内容（至少 {MIN_CHINESE_CHARS} 个中文字符）"
        )
    if INTERNAL_PLACEHOLDER_RE.search(text):
        raise ValidationError(f"{paper_id}: {field} 含内部占位/流程标记，不可发布给读者")
    return text


STRICT_TAG_DIMS = {"方向", "应用", "硬件"}
FREE_TAG_DIMS = {"模型"}
ALL_TAG_DIMS = STRICT_TAG_DIMS | FREE_TAG_DIMS


def load_tag_vocab() -> dict[str, set[str]]:
    """Read data/tags.yaml into {dimension: set(values)}."""
    import yaml

    p = ROOT / "data" / "tags.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return {dim: set(str(v) for v in vals) for dim, vals in data.items()}


def normalize_tags(value, paper_id: str, vocab: dict[str, set[str]]) -> list[str]:
    """Tags are `维度:值` strings. 方向/应用/硬件 strict (must be in vocab);
    模型 semi-free. 1-8 tags, multi-dimension allowed."""
    if not isinstance(value, list):
        raise ValidationError(f"{paper_id}: tags must be an array")
    tags: list[str] = []
    for raw_tag in value:
        tag = text_value(raw_tag)
        if not tag:
            continue
        if ":" not in tag:
            raise ValidationError(
                f"{paper_id}: tag {tag!r} must be '维度:值' (e.g. 方向:量化); "
                f"dims: {sorted(ALL_TAG_DIMS)}"
            )
        dim, val = tag.split(":", 1)
        dim = dim.strip()
        val = val.strip()
        if dim not in ALL_TAG_DIMS:
            raise ValidationError(
                f"{paper_id}: tag dim {dim!r} not in {sorted(ALL_TAG_DIMS)}"
            )
        if dim in STRICT_TAG_DIMS and val not in vocab.get(dim, set()):
            raise ValidationError(
                f"{paper_id}: {dim}:{val} not in taxonomy (see data/tags.yaml); "
                "propose new tags in score_reason and add to data/tags.yaml first"
            )
        full = f"{dim}:{val}"
        if full not in tags:
            tags.append(full)
    if not tags:
        raise ValidationError(f"{paper_id}: tags must contain at least one item")
    if len(tags) > 8:
        raise ValidationError(f"{paper_id}: tags must contain at most 8 items")
    return tags


def load_last_run_ids() -> set[str]:
    """Read data/.last_run_papers.json (written by publish_results.py) for cross-run dedup."""
    p = ROOT / "data" / ".last_run_papers.json"
    if not p.exists():
        return set()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    ids = data.get("paper_ids", [])
    return set(str(i) for i in ids) if isinstance(ids, list) else set()


def write_last_run_ids(run_id: str, paper_ids: list[str]) -> None:
    """Persist this run's paper ids so the next validate can cross-run dedup."""
    p = ROOT / "data" / ".last_run_papers.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"run_id": run_id, "paper_ids": list(paper_ids)}
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def validate_url(value: str, field: str, paper_id: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError(f"{paper_id}: {field} must be an http(s) URL")
    return value


def is_authoritative_affiliation_evidence_url(value: str) -> bool:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if not any(host == domain or host.endswith("." + domain) for domain in AFFILIATION_EVIDENCE_DOMAINS):
        return False
    path = parsed.path or "/"
    if host == "arxiv.org" or host.endswith(".arxiv.org"):
        return path.startswith("/pdf/")
    return path != "/" or bool(parsed.query)


def is_link_alive(url: str, timeout: int = 5) -> bool:
    """Return True if ``url`` responds with HTTP status < 400.

    HEAD first; falls back to GET when the server rejects HEAD. Some sites
    return 403/400 (not just 405) for HEAD while GET succeeds, so any HEAD
    HTTPError retries GET as the ground truth. Network errors (offline / DNS
    failure) count as alive to avoid false-killing papers when the validator
    runs offline; timeouts count as dead.
    """
    # A Mozilla-compatible UA is required: WAF-protected vendor sites
    # (e.g. qualcomm.com) block the default Python-urllib UA with 403,
    # which would falsely mark live pages as dead.
    headers = {"User-Agent": "Mozilla/5.0 (compatible; edge-agent-validator/1.0)"}
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status < 400
        except urllib.error.HTTPError as exc:
            if method == "HEAD":
                # Server rejected HEAD (405/403/400). GET is ground truth;
                # a truly dead URL fails GET too, so no false positives.
                continue
            # 429 (Too Many Requests) / 503 (Service Unavailable) are transient
            # rate-limit/overload — the URL is fine, the server is throttling
            # (e.g. huggingface.co/papers under rapid sequential HEAD). Treat as
            # alive so batch validation doesn't false-kill real papers.
            if exc.code in (429, 503):
                print(f"warning: link check got {exc.code} (rate-limit) for {url} (treating as alive)", file=sys.stderr)
                return True
            return exc.code < 400
        except (TimeoutError, socket.timeout):
            print(f"warning: link check timed out for {url} (treating as alive)", file=sys.stderr)
            return True
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                print(f"warning: link check timed out for {url} (treating as alive)", file=sys.stderr)
                return True
            print(f"warning: link check skipped for {url} (network unavailable)", file=sys.stderr)
            return True
    return False


def is_official_source_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in OFFICIAL_SOURCE_DOMAINS)


def is_github_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host == "github.com" or host.endswith(".github.com")


def fetch_arxiv_dates(url: str, timeout: int = 8) -> tuple[date | None, date | None]:
    """Query arXiv for both v1 submitted and latest revision dates.

    Returns ``(None, None)`` when metadata is unavailable; callers warn and
    skip the remote date cross-check.
    """
    m = ARXIV_URL_RE.match(url)
    if not m:
        return None, None
    arxiv_id = re.sub(r"v\d+$", "", m.group(1))
    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; edge-agent-validator/1.0)"}
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
    except (urllib.error.URLError, TimeoutError, socket.timeout):
        return None, None

    def parse_atom_date(field: str) -> date | None:
        match = re.search(rf"<{field}>([^<]+)</{field}>", body)
        if not match:
            return None
        try:
            return datetime.fromisoformat(match.group(1).replace("Z", "+00:00")).date()
        except ValueError:
            return None

    return parse_atom_date("published"), parse_atom_date("updated")


def fetch_arxiv_published_date(url: str, timeout: int = 8) -> date | None:
    """Backward-compatible helper for callers that only need the v1 date."""
    return fetch_arxiv_dates(url, timeout=timeout)[0]


def normalize_paper(raw: dict, today: date, seen_ids: set[str], vocab: dict[str, set[str]], skip_network: bool = False) -> dict:
    if not isinstance(raw, dict):
        raise ValidationError("paper item must be an object")

    paper = dict(raw)
    if "paper_url" not in paper and "url" in paper:
        paper["paper_url"] = paper["url"]

    missing = [field for field in REQUIRED_PAPER_FIELDS if text_value(paper.get(field)) == "" and not isinstance(paper.get(field), bool)]
    # open_source is a bool: text_value(False)=="" would falsely flag it; treat bool as present.
    paper_id = text_value(paper.get("id")) or "<missing-id>"
    if missing:
        raise ValidationError(f"{paper_id}: missing required fields: {', '.join(missing)}")
    if "edge_agent_evidence" not in paper:
        raise ValidationError(f"{paper_id}: missing required field: edge_agent_evidence")

    edge_agent_scope = text_value(paper.get("edge_agent_scope"))
    if edge_agent_scope not in ALLOWED_EDGE_AGENT_SCOPES:
        allowed = ", ".join(sorted(ALLOWED_EDGE_AGENT_SCOPES))
        raise ValidationError(f"{paper_id}: edge_agent_scope must be one of: {allowed}")
    if edge_agent_scope == "待核实":
        raise ValidationError(f"{paper_id}: edge_agent_scope=待核实，不可发布；主 Agent 必须阅读来源后分类")
    edge_agent_evidence = text_value(paper.get("edge_agent_evidence"))

    abstract = require_reader_facing_chinese(paper.get("abstract"), "abstract", paper_id)
    title_zh = text_value(paper.get("title_zh"))
    if title_zh:
        if len(CJK_RE.findall(title_zh)) < 2:
            raise ValidationError(
                f"{paper_id}: title_zh 必须是简短中文项目名（至少 2 个中文字符）"
            )
        if len(title_zh) > 40:
            raise ValidationError(f"{paper_id}: title_zh 不能超过 40 个字符")
        if INTERNAL_PLACEHOLDER_RE.search(title_zh):
            raise ValidationError(f"{paper_id}: title_zh 含内部占位/流程标记，不可发布给读者")
        if title_zh == abstract:
            raise ValidationError(f"{paper_id}: title_zh 必须是项目名，不能直接复用 abstract")
    for field in ("effects", "mechanism"):
        if INTERNAL_PLACEHOLDER_RE.search(text_value(paper.get(field))):
            raise ValidationError(f"{paper_id}: {field} 含内部占位/流程标记，不可发布给读者")

    recommendation = text_value(paper.get("recommendation")) or "纳入"
    if recommendation not in {"纳入", "推荐"}:
        raise ValidationError(f"{paper_id}: recommendation must be 纳入 or 推荐")
    if recommendation == "推荐" and not title_zh:
        raise ValidationError(f"{paper_id}: recommendation=推荐 时必须填写 title_zh 中文项目名")
    recommendation_reason = text_value(paper.get("recommendation_reason"))
    if recommendation == "推荐":
        recommendation_reason = require_reader_facing_chinese(
            recommendation_reason, "recommendation_reason", paper_id
        )

    if paper_id in seen_ids:
        raise ValidationError(f"{paper_id}: duplicate paper id")
    seen_ids.add(paper_id)

    source_tier = text_value(paper.get("source_tier"))
    if source_tier not in ALLOWED_SOURCE_TIERS:
        allowed = ", ".join(sorted(ALLOWED_SOURCE_TIERS))
        raise ValidationError(f"{paper_id}: source_tier must be one of: {allowed}")

    tags = normalize_tags(paper.get("tags"), paper_id, vocab)
    is_direct_edge_agent = edge_agent_scope in DIRECT_EDGE_AGENT_SCOPES
    has_direct_edge_tag = DIRECT_EDGE_AGENT_TAG in tags
    if is_direct_edge_agent:
        edge_agent_evidence = require_reader_facing_chinese(
            edge_agent_evidence, "edge_agent_evidence", paper_id
        )
        if not has_direct_edge_tag:
            raise ValidationError(
                f"{paper_id}: 真正端侧 Agent 必须包含 {DIRECT_EDGE_AGENT_TAG} 标签"
            )
        if recommendation != "推荐":
            raise ValidationError(
                f"{paper_id}: 真正端侧 Agent（{edge_agent_scope}）必须设置 recommendation=推荐"
            )
    elif has_direct_edge_tag:
        raise ValidationError(
            f"{paper_id}: edge_agent_scope=非端侧Agent 时不得使用 {DIRECT_EDGE_AGENT_TAG} 标签"
        )
    elif edge_agent_evidence:
        raise ValidationError(
            f"{paper_id}: 非端侧 Agent 的 edge_agent_evidence 必须为空"
        )

    try:
        paper_date = datetime.fromisoformat(text_value(paper.get("date"))).date()
    except ValueError as exc:
        raise ValidationError(f"{paper_id}: invalid date {paper.get('date')!r}") from exc

    cutoff, _, _ = collection_window(today)
    if paper_date < cutoff or paper_date > today:
        raise ValidationError(f"{paper_id}: date {paper_date} outside window [{cutoff} .. {today}]")

    try:
        score = int(paper.get("score"))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{paper_id}: score must be an integer") from exc
    if score < 0 or score > 20:
        raise ValidationError(f"{paper_id}: score must be between 0 and 20")

    score_dims: dict[str, int] = {}
    dim_total = 0
    for field, maximum in SCORE_DIMENSIONS:
        try:
            value = int(paper.get(field))
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{paper_id}: {field} must be an integer") from exc
        if value < 0 or value > maximum:
            raise ValidationError(f"{paper_id}: {field} must be between 0 and {maximum}")
        score_dims[field] = value
        dim_total += value
    if dim_total != score:
        raise ValidationError(
            f"{paper_id}: score {score} must equal sum of 2 dimensions ({dim_total})"
        )
    if is_direct_edge_agent and score_dims["score_relevance"] < 8:
        raise ValidationError(
            f"{paper_id}: 真正端侧 Agent 的 score_relevance 必须为 8-10"
        )

    paper_url = validate_url(text_value(paper.get("paper_url")), "paper_url", paper_id)
    if not skip_network and not is_link_alive(paper_url):
        raise ValidationError(f"{paper_id}: paper_url is dead/404")
    # arXiv papers: verify the JSON date against the real submitted date to
    # block agents from re-dating an old paper into the window. Skipped on the
    # server side (skip_network) — the CLI pre-validate already did it.
    arxiv_date_basis = text_value(paper.get("arxiv_date_basis")) or "submitted"
    if arxiv_date_basis not in {"submitted", "updated"}:
        raise ValidationError(f"{paper_id}: arxiv_date_basis must be submitted or updated")
    arxiv_revision_note = text_value(paper.get("arxiv_revision_note"))
    if "arxiv.org" in paper_url.lower() and arxiv_date_basis == "updated":
        arxiv_revision_note = require_reader_facing_chinese(
            arxiv_revision_note, "arxiv_revision_note", paper_id
        )
    if not skip_network and "arxiv.org" in paper_url.lower():
        published, updated = fetch_arxiv_dates(paper_url)
        expected_date = updated if arxiv_date_basis == "updated" else published
        if expected_date is not None:
            if expected_date != paper_date:
                raise ValidationError(
                    f"{paper_id}: date {paper_date} mismatches arXiv {arxiv_date_basis} date {expected_date}"
                )
        else:
            print(
                f"warning: arXiv date check skipped for {paper_url} (network unavailable)",
                file=sys.stderr,
            )
    wiki_url = text_value(paper.get("wiki_url"))
    if wiki_url:
        wiki_url = validate_url(wiki_url, "wiki_url", paper_id)
        if not is_link_alive(wiki_url):
            raise ValidationError(f"{paper_id}: wiki_url is dead/404")

    vendors = text_value(paper.get("vendors"))
    authors = text_value(paper.get("authors"))
    score_reason = text_value(paper.get("score_reason"))
    if INTERNAL_PLACEHOLDER_RE.search(score_reason):
        raise ValidationError(f"{paper_id}: score_reason 含内部占位/流程标记，不可发布给读者")
    affiliation_evidence_url = text_value(paper.get("affiliation_evidence_url"))
    if source_tier == COMPANY_TIER and not vendors:
        raise ValidationError(f"{paper_id}: source_tier=公司项目 requires non-empty vendors")
    if source_tier == COMPANY_TIER:
        if not affiliation_evidence_url:
            raise ValidationError(
                f"{paper_id}: source_tier=公司项目 requires affiliation_evidence_url"
            )
        affiliation_evidence_url = validate_url(
            affiliation_evidence_url, "affiliation_evidence_url", paper_id
        )
        if not is_authoritative_affiliation_evidence_url(affiliation_evidence_url):
            raise ValidationError(
                f"{paper_id}: affiliation_evidence_url must be authoritative affiliation evidence"
            )
        vendor_terms = [term.strip() for term in re.split(r"[,;/|&]", vendors) if term.strip()]
        if not vendor_terms:
            raise ValidationError(
                f"{paper_id}: source_tier={COMPANY_TIER} requires at least one valid vendors name"
            )
        missing_vendor_terms = [
            term
            for term in vendor_terms
            if not re.search(
                rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])",
                score_reason,
                re.IGNORECASE,
            )
        ]
        if missing_vendor_terms:
            raise ValidationError(
                f"{paper_id}: score_reason must explain affiliation evidence for every vendor; "
                f"missing={', '.join(missing_vendor_terms)}"
            )
        if not skip_network and not is_link_alive(affiliation_evidence_url):
            raise ValidationError(f"{paper_id}: affiliation_evidence_url is dead/404")
    if source_tier == OFFICIAL_TIER and not is_official_source_url(paper_url):
        raise ValidationError(f"{paper_id}: source_tier=官方动态 requires an official vendor domain URL")
    if source_tier == OSS_TIER and not is_github_url(paper_url):
        raise ValidationError(f"{paper_id}: source_tier=开源大项目 requires a github.com URL")
    if source_tier == OSS_TIER and not is_required_github_project(paper_url):
        raise ValidationError(
            f"{paper_id}: source_tier=开源大项目 requires a whitelisted GitHub big project"
        )

    open_source = bool_value(paper.get("open_source"))
    candidate_source = text_value(paper.get("candidate_source"))
    candidate_ref = text_value(paper.get("candidate_ref"))

    return {
        "id": paper_id,
        "title": text_value(paper.get("title")),
        "title_zh": title_zh,
        "abstract": abstract,
        "effects": text_value(paper.get("effects")),
        "mechanism": text_value(paper.get("mechanism")),
        "paper_url": paper_url,
        "date": paper_date.isoformat(),
        "score": score,
        "score_relevance": score_dims["score_relevance"],
        "score_contribution": score_dims["score_contribution"],
        "score_reason": score_reason,
        "source_tier": source_tier,
        "open_source": open_source,
        "tags": tags,
        "edge_agent_scope": edge_agent_scope,
        "edge_agent_evidence": edge_agent_evidence,
        "insight_person": text_value(paper.get("insight_person")),
        "wiki_url": wiki_url,
        "authors": authors,
        "vendors": vendors,
        "affiliation_evidence_url": affiliation_evidence_url,
        "candidate_source": candidate_source,
        "candidate_ref": candidate_ref,
        "venue": text_value(paper.get("venue")),
        "recommendation": recommendation,
        "recommendation_reason": recommendation_reason,
        "arxiv_date_basis": arxiv_date_basis,
        "arxiv_revision_note": arxiv_revision_note,
    }


def validate_payload(
    payload: dict,
    today: str | date | None = None,
    skip_network: bool = False,
    require_collection_manifest: bool = False,
) -> dict:
    today_date = parse_today(today)
    if not isinstance(payload, dict):
        raise ValidationError("payload must be an object")

    collection_manifest = payload.get("collection_manifest")
    if require_collection_manifest and not isinstance(collection_manifest, dict):
        raise ValidationError("missing collection_manifest coverage attestation")
    if isinstance(collection_manifest, dict):
        try:
            collection_manifest = validate_collection_manifest(collection_manifest, today=today_date)
        except CollectionCoverageError as exc:
            raise ValidationError(f"invalid collection_manifest: {exc}") from exc

    run_id = text_value(payload.get("run_id"))
    if not run_id:
        raise ValidationError("missing run_id")

    papers = payload.get("papers")
    if not isinstance(papers, list) or not papers:
        raise ValidationError("papers must be a non-empty array")

    vocab = load_tag_vocab()
    seen_ids: set[str] = set()
    normalized_papers = [normalize_paper(item, today_date, seen_ids, vocab, skip_network) for item in papers]
    if isinstance(collection_manifest, dict):
        try:
            validate_run_candidate_lineage(normalized_papers, collection_manifest)
        except CollectionCoverageError as exc:
            raise ValidationError(f"invalid candidate lineage: {exc}") from exc

    last_ids = load_last_run_ids()
    if last_ids:
        recurred = [p["id"] for p in normalized_papers if p["id"] in last_ids]
        if recurred:
            print(
                f"warning: {len(recurred)} paper(s) appeared in the last run "
                f"(verify these are genuinely new, not re-dumped): {recurred}",
                file=sys.stderr,
            )

    normalized = {
        "run_id": run_id,
        "generated_at": text_value(payload.get("generated_at")),
        "papers": normalized_papers,
    }
    if isinstance(collection_manifest, dict):
        normalized["collection_manifest"] = collection_manifest
    return normalized


def load_and_validate(path: str | Path, today: str | date | None = None) -> dict:
    return validate_payload(load_run_file(path), today=today)
