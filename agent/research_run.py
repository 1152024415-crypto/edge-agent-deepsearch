#!/usr/bin/env python3
"""Validation helpers for child-agent research run JSON files."""

from __future__ import annotations

import json
import socket
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse


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
    "source_type",
    "category",
    "keywords",
    "score_relevance",
    "score_vendor",
    "score_contribution",
    "score_quality",
    "score_recency",
)

# 5 维评分: 字段名 -> 满分。score 必须等于 5 维之和。
SCORE_DIMENSIONS = (
    ("score_relevance", 35),
    ("score_vendor", 25),
    ("score_contribution", 20),
    ("score_quality", 15),
    ("score_recency", 5),
)

ACADEMIC_SOURCE_TYPE = "学术论文"
OFFICIAL_SOURCE_TYPES = {"官方技术博客", "官方产品发布"}
ALLOWED_SOURCE_TYPES = {ACADEMIC_SOURCE_TYPE, *OFFICIAL_SOURCE_TYPES}
ALLOWED_CATEGORIES = {"应用", "框架", "算法"}

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
    "honor.com",
    "alibabacloud.com",
    "qwenlm.github.io",
    "mistral.ai",
)

MAJOR_VENDOR_TOKENS = (
    "apple",
    "google",
    "microsoft",
    "openai",
    "anthropic",
    "meta",
    "samsung",
    "huawei",
    "qualcomm",
    "mediatek",
    "xiaomi",
    "oppo",
    "vivo",
    "honor",
    "alibaba",
    "qwen",
    "mistral",
    "modelbest",
)


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


def validate_url(value: str, field: str, paper_id: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError(f"{paper_id}: {field} must be an http(s) URL")
    return value


def is_link_alive(url: str, timeout: int = 5) -> bool:
    """Return True if ``url`` responds with HTTP status < 400.

    HEAD first; falls back to GET when the server rejects HEAD (405).
    Network errors (offline / DNS failure) count as alive to avoid
    false-killing papers when the validator runs offline; timeouts count
    as dead.
    """
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status < 400
        except urllib.error.HTTPError as exc:
            if method == "HEAD" and exc.code == 405:
                continue
            return exc.code < 400
        except (TimeoutError, socket.timeout):
            return False
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                return False
            print(f"warning: link check skipped for {url} (network unavailable)", file=sys.stderr)
            return True
    return False


def is_official_source_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in OFFICIAL_SOURCE_DOMAINS)


def has_major_vendor_marker(*values: str) -> bool:
    text = " ".join(values).lower()
    return any(token in text for token in MAJOR_VENDOR_TOKENS)


def normalize_keywords(value, paper_id: str) -> list[str]:
    if not isinstance(value, list):
        raise ValidationError(f"{paper_id}: keywords must be an array")
    keywords: list[str] = []
    for raw_keyword in value:
        keyword = text_value(raw_keyword)
        if not keyword:
            continue
        if "\n" in keyword or len(keyword) > 24:
            raise ValidationError(f"{paper_id}: keyword {keyword!r} must be short")
        if keyword not in keywords:
            keywords.append(keyword)
    if not keywords:
        raise ValidationError(f"{paper_id}: keywords must contain at least one item")
    if len(keywords) > 8:
        raise ValidationError(f"{paper_id}: keywords must contain at most 8 items")
    return keywords


def normalize_paper(raw: dict, today: date, seen_ids: set[str]) -> dict:
    if not isinstance(raw, dict):
        raise ValidationError("paper item must be an object")

    paper = dict(raw)
    if "paper_url" not in paper and "url" in paper:
        paper["paper_url"] = paper["url"]

    missing = [field for field in REQUIRED_PAPER_FIELDS if text_value(paper.get(field)) == ""]
    paper_id = text_value(paper.get("id")) or "<missing-id>"
    if missing:
        raise ValidationError(f"{paper_id}: missing required fields: {', '.join(missing)}")

    if paper_id in seen_ids:
        raise ValidationError(f"{paper_id}: duplicate paper id")
    seen_ids.add(paper_id)

    source_type = text_value(paper.get("source_type"))
    if source_type not in ALLOWED_SOURCE_TYPES:
        allowed = ", ".join(sorted(ALLOWED_SOURCE_TYPES))
        raise ValidationError(f"{paper_id}: source_type must be one of: {allowed}")

    category = text_value(paper.get("category"))
    if category not in ALLOWED_CATEGORIES:
        allowed = ", ".join(sorted(ALLOWED_CATEGORIES))
        raise ValidationError(f"{paper_id}: category must be one of: {allowed}")
    keywords = normalize_keywords(paper.get("keywords"), paper_id)

    try:
        paper_date = datetime.fromisoformat(text_value(paper.get("date"))).date()
    except ValueError as exc:
        raise ValidationError(f"{paper_id}: invalid date {paper.get('date')!r}") from exc

    cutoff = today - timedelta(days=7)
    if paper_date < cutoff or paper_date > today:
        raise ValidationError(f"{paper_id}: date {paper_date} outside window [{cutoff} .. {today}]")

    try:
        score = int(paper.get("score"))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{paper_id}: score must be an integer") from exc
    if score < 0 or score > 100:
        raise ValidationError(f"{paper_id}: score must be between 0 and 100")

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
            f"{paper_id}: score {score} must equal sum of 5 dimensions ({dim_total})"
        )

    paper_url = validate_url(text_value(paper.get("paper_url")), "paper_url", paper_id)
    if not is_link_alive(paper_url):
        raise ValidationError(f"{paper_id}: paper_url is dead/404")
    wiki_url = text_value(paper.get("wiki_url"))
    if wiki_url:
        wiki_url = validate_url(wiki_url, "wiki_url", paper_id)
        if not is_link_alive(wiki_url):
            raise ValidationError(f"{paper_id}: wiki_url is dead/404")

    is_major_vendor_official = bool_value(paper.get("is_major_vendor_official"))
    vendors = text_value(paper.get("vendors"))
    authors = text_value(paper.get("authors"))
    if source_type in OFFICIAL_SOURCE_TYPES:
        if not is_major_vendor_official:
            raise ValidationError(f"{paper_id}: official vendor source must set is_major_vendor_official=true")
        if not is_official_source_url(paper_url):
            raise ValidationError(f"{paper_id}: official vendor source must use an official vendor URL")
    if is_major_vendor_official and not (is_official_source_url(paper_url) or has_major_vendor_marker(vendors, authors)):
        raise ValidationError(f"{paper_id}: is_major_vendor_official requires an official URL or major vendor marker")

    return {
        "id": paper_id,
        "title": text_value(paper.get("title")),
        "abstract": text_value(paper.get("abstract")),
        "effects": text_value(paper.get("effects")),
        "mechanism": text_value(paper.get("mechanism")),
        "paper_url": paper_url,
        "date": paper_date.isoformat(),
        "score": score,
        "score_reason": text_value(paper.get("score_reason")),
        "source_type": source_type,
        "is_major_vendor_official": is_major_vendor_official,
        "category": category,
        "keywords": keywords,
        "score_relevance": score_dims["score_relevance"],
        "score_vendor": score_dims["score_vendor"],
        "score_contribution": score_dims["score_contribution"],
        "score_quality": score_dims["score_quality"],
        "score_recency": score_dims["score_recency"],
        "insight_person": text_value(paper.get("insight_person")),
        "wiki_url": wiki_url,
        "authors": authors,
        "vendors": vendors,
        "venue": text_value(paper.get("venue")),
        "recommendation": text_value(paper.get("recommendation")) or "纳入",
    }


def validate_payload(payload: dict, today: str | date | None = None) -> dict:
    today_date = parse_today(today)
    if not isinstance(payload, dict):
        raise ValidationError("payload must be an object")

    run_id = text_value(payload.get("run_id"))
    if not run_id:
        raise ValidationError("missing run_id")

    papers = payload.get("papers")
    if not isinstance(papers, list) or not papers:
        raise ValidationError("papers must be a non-empty array")

    seen_ids: set[str] = set()
    normalized_papers = [normalize_paper(item, today_date, seen_ids) for item in papers]

    return {
        "run_id": run_id,
        "generated_at": text_value(payload.get("generated_at")),
        "papers": normalized_papers,
    }


def load_and_validate(path: str | Path, today: str | date | None = None) -> dict:
    return validate_payload(load_run_file(path), today=today)
