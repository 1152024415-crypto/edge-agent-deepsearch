"""Validation and loading for the independently edited community radar."""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

SOURCES = ("X", "Reddit", "Hacker News", "厂商论坛", "开发者论坛")
COVERAGE_STATUSES = {"found", "no_match", "limited", "unavailable"}
DEVICE_SCOPES = {"手机", "PC", "其他端侧", "通用技术"}
VERIFICATION_STATUSES = {"仅线索", "已回链原始材料", "已进入正式周报"}
DEVICE_PRIORITY = {"手机": 0, "PC": 1, "其他端侧": 2, "通用技术": 3}
_CJK_RE = re.compile(r"[\u3400-\u9fff]")


class CommunityValidationError(ValueError):
    pass


def _http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _parse_published_date(value: str) -> date:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except (AttributeError, TypeError, ValueError) as exc:
        raise CommunityValidationError(f"published_at 不是 ISO 时间：{value!r}") from exc


def validate_community(payload: dict, *, today: date | None = None) -> dict:
    today = today or date.today()
    if not isinstance(payload, dict):
        raise CommunityValidationError("community radar 必须是 JSON object")

    window = payload.get("window") or {}
    try:
        start = date.fromisoformat(window["start"])
        end = date.fromisoformat(window["end"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CommunityValidationError("window.start/end 必须是 ISO 日期") from exc
    if end != today or (end - start).days != 6:
        raise CommunityValidationError("community radar 必须覆盖截至 today 的 7 个自然日")

    coverage = payload.get("coverage")
    if not isinstance(coverage, list):
        raise CommunityValidationError("coverage 必须是数组")
    seen_sources = set()
    normalized_coverage = []
    for record in coverage:
        source = str((record or {}).get("source") or "").strip()
        status = str((record or {}).get("status") or "").strip()
        note = str((record or {}).get("note") or "").strip()
        if source not in SOURCES or source in seen_sources:
            raise CommunityValidationError(f"coverage source 非法或重复：{source!r}")
        if status not in COVERAGE_STATUSES:
            raise CommunityValidationError(f"coverage status 非法：{status!r}")
        if not note:
            raise CommunityValidationError(f"coverage {source} 必须说明结果")
        seen_sources.add(source)
        normalized_coverage.append({"source": source, "status": status, "note": note})
    if seen_sources != set(SOURCES):
        missing = ", ".join(source for source in SOURCES if source not in seen_sources)
        raise CommunityValidationError(f"coverage 缺少来源：{missing}")

    items = payload.get("items")
    if not isinstance(items, list):
        raise CommunityValidationError("items 必须是数组")
    normalized_items = []
    ids = set()
    for index, raw in enumerate(items):
        item = dict(raw or {})
        item_id = str(item.get("id") or "").strip()
        if not item_id or item_id in ids:
            raise CommunityValidationError(f"items[{index}].id 缺失或重复")
        ids.add(item_id)
        source = str(item.get("source") or "").strip()
        device_scope = str(item.get("device_scope") or "").strip()
        verification = str(item.get("verification") or "").strip()
        if source not in SOURCES:
            raise CommunityValidationError(f"items[{index}].source 非法")
        if device_scope not in DEVICE_SCOPES:
            raise CommunityValidationError(f"items[{index}].device_scope 非法")
        if verification not in VERIFICATION_STATUSES:
            raise CommunityValidationError(f"items[{index}].verification 非法")
        if not _http_url(str(item.get("url") or "")):
            raise CommunityValidationError(f"items[{index}].url 必须是 HTTP(S) 直达链接")
        published_date = _parse_published_date(item.get("published_at"))
        if not start <= published_date <= end:
            raise CommunityValidationError(f"items[{index}] 日期超出社区窗口")
        for field in ("title_zh", "summary_zh", "why_it_matters"):
            value = str(item.get(field) or "").strip()
            if len(value) < 4 or not _CJK_RE.search(value):
                raise CommunityValidationError(f"items[{index}].{field} 必须是可读中文")
            item[field] = value
        evidence_url = str(item.get("evidence_url") or "").strip()
        if evidence_url and not _http_url(evidence_url):
            raise CommunityValidationError(f"items[{index}].evidence_url 非法")
        item.update({
            "id": item_id,
            "source": source,
            "author": str(item.get("author") or "").strip(),
            "published_at": str(item["published_at"]),
            "device_scope": device_scope,
            "topic": str(item.get("topic") or "").strip(),
            "verification": verification,
            "evidence_url": evidence_url,
        })
        normalized_items.append(item)

    normalized_items.sort(key=lambda item: (
        DEVICE_PRIORITY[item["device_scope"]],
        -datetime.fromisoformat(item["published_at"].replace("Z", "+00:00")).timestamp(),
        item["id"],
    ))
    return {"window": {"start": start.isoformat(), "end": end.isoformat()}, "coverage": normalized_coverage, "items": normalized_items}


def empty_community(today: date | None = None, note: str = "社区数据文件不存在") -> dict:
    today = today or date.today()
    start = date.fromordinal(today.toordinal() - 6)
    return {
        "window": {"start": start.isoformat(), "end": today.isoformat()},
        "coverage": [
            {"source": source, "status": "unavailable", "note": note}
            for source in SOURCES
        ],
        "items": [],
    }


def load_community(path: Path, *, today: date | None = None) -> dict:
    path = Path(path)
    if not path.exists():
        return empty_community(today)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CommunityValidationError(f"无法读取 community radar：{exc}") from exc
    return validate_community(payload, today=today)
