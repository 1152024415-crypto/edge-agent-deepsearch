"""SQLite storage for accepted research papers."""

from __future__ import annotations

import json
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "agent"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import research_run


PAPER_COLUMNS = (
    "id",
    "run_id",
    "title",
    "abstract",
    "effects",
    "mechanism",
    "paper_url",
    "date",
    "score",
    "score_relevance",
    "score_contribution",
    "score_reason",
    "source_tier",
    "open_source",
    "tags",
    "insight_person",
    "wiki_url",
    "authors",
    "vendors",
    "venue",
    "recommendation",
    "detail",
    "updated_at",
)

# source_tier 排序优先级（数字小排前）：官方动态 > 开源大项目 > 公司项目 > 学校顶会 > 学校预印本
TIER_CASE = (
    "CASE source_tier "
    "WHEN '官方动态' THEN 0 WHEN '开源大项目' THEN 1 "
    "WHEN '公司项目' THEN 2 WHEN '学校顶会' THEN 3 WHEN '学校预印本' THEN 4 ELSE 9 END"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(db_path)) as conn:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS research_runs (
                    run_id TEXT PRIMARY KEY,
                    generated_at TEXT,
                    received_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS papers (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    abstract TEXT NOT NULL,
                    effects TEXT NOT NULL,
                    mechanism TEXT NOT NULL,
                    paper_url TEXT NOT NULL,
                    date TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    score_relevance INTEGER,
                    score_contribution INTEGER,
                    score_reason TEXT,
                    source_tier TEXT NOT NULL,
                    open_source INTEGER NOT NULL DEFAULT 0,
                    tags TEXT,
                    insight_person TEXT,
                    wiki_url TEXT,
                    authors TEXT,
                    vendors TEXT,
                    venue TEXT,
                    recommendation TEXT,
                    detail TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(papers)").fetchall()}
            # New-schema columns added to legacy DBs that still carry old score_* columns.
            for field in ("score_relevance", "score_contribution", "score_reason"):
                if field not in columns:
                    conn.execute(f"ALTER TABLE papers ADD COLUMN {field} INTEGER")
            if "source_tier" not in columns:
                conn.execute("ALTER TABLE papers ADD COLUMN source_tier TEXT")
            if "open_source" not in columns:
                conn.execute("ALTER TABLE papers ADD COLUMN open_source INTEGER NOT NULL DEFAULT 0")
            if "tags" not in columns:
                conn.execute("ALTER TABLE papers ADD COLUMN tags TEXT")
            if "detail" not in columns:
                conn.execute("ALTER TABLE papers ADD COLUMN detail TEXT")
            if "recommendation" not in columns:
                conn.execute("ALTER TABLE papers ADD COLUMN recommendation TEXT")


def upsert_run(db_path: Path, payload: dict) -> dict:
    # EDGE_TODAY env (YYYY-MM-DD) overrides the "today" used for the 7-day
    # window check — lets an expanded-window run (e.g. 07-17~07-24 published
    # on 07-25, where 07-17 is 8 days back from real today) pass by treating
    # the window END as today. Same env-override pattern as EDGE_WEEKS_DIR.
    import os
    today_override = os.environ.get("EDGE_TODAY")
    normalized = research_run.validate_payload(payload, skip_network=True, today=today_override)
    timestamp = now_iso()
    with closing(connect(db_path)) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO research_runs (run_id, generated_at, received_at)
                VALUES (?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    generated_at = excluded.generated_at,
                    received_at = excluded.received_at
                """,
                (normalized["run_id"], normalized.get("generated_at", ""), timestamp),
            )
            for paper in normalized["papers"]:
                values = {**paper, "run_id": normalized["run_id"], "updated_at": timestamp}
                values["open_source"] = int(bool(values.get("open_source")))
                values["tags"] = json.dumps(values.get("tags", []), ensure_ascii=False)
                conn.execute(
                    """
                    INSERT INTO papers (
                        id, run_id, title, abstract, effects, mechanism, paper_url, date, score,
                        score_relevance, score_contribution, score_reason, source_tier, open_source,
                        tags, insight_person, wiki_url, authors, vendors, venue, recommendation,
                        updated_at
                    )
                    VALUES (
                        :id, :run_id, :title, :abstract, :effects, :mechanism, :paper_url, :date,
                        :score, :score_relevance, :score_contribution, :score_reason, :source_tier,
                        :open_source, :tags, :insight_person, :wiki_url, :authors, :vendors, :venue,
                        :recommendation, :updated_at
                    )
                    ON CONFLICT(id) DO UPDATE SET
                        run_id = excluded.run_id,
                        title = excluded.title,
                        abstract = excluded.abstract,
                        effects = excluded.effects,
                        mechanism = excluded.mechanism,
                        paper_url = excluded.paper_url,
                        date = excluded.date,
                        score = excluded.score,
                        score_relevance = excluded.score_relevance,
                        score_contribution = excluded.score_contribution,
                        score_reason = excluded.score_reason,
                        source_tier = excluded.source_tier,
                        open_source = excluded.open_source,
                        tags = excluded.tags,
                        insight_person = excluded.insight_person,
                        wiki_url = excluded.wiki_url,
                        authors = excluded.authors,
                        vendors = excluded.vendors,
                        venue = excluded.venue,
                        recommendation = excluded.recommendation,
                        updated_at = excluded.updated_at
                    """,
                    values,
                )
    return {"ok": True, "run_id": normalized["run_id"], "accepted": len(normalized["papers"])}


def _attach_row(paper: dict) -> dict:
    paper["open_source"] = bool(paper.get("open_source"))
    try:
        tags = json.loads(paper.get("tags") or "[]")
    except json.JSONDecodeError:
        tags = []
    paper["tags"] = tags if isinstance(tags, list) else []
    return paper


def list_papers(db_path: Path, sort: str = "score") -> list[dict]:
    order_by = (
        f"{TIER_CASE} ASC, score DESC, date DESC, title ASC"
        if sort != "date"
        else f"{TIER_CASE} ASC, date DESC, score DESC, title ASC"
    )
    with closing(connect(db_path)) as conn:
        latest_run = conn.execute(
            """
            SELECT run_id
            FROM research_runs
            ORDER BY received_at DESC, run_id DESC
            LIMIT 1
            """
        ).fetchone()
        if latest_run is None:
            return []
        rows = conn.execute(
            f"SELECT {', '.join(PAPER_COLUMNS)} FROM papers WHERE run_id = ? ORDER BY {order_by}",
            (latest_run["run_id"],),
        ).fetchall()
    return [_attach_row(dict(row)) for row in rows]


def update_insight(db_path: Path, payload: dict) -> dict:
    paper_id = str(payload.get("paper_id", "")).strip()
    if not paper_id:
        raise research_run.ValidationError("paper_id is required")
    insight_person = str(payload.get("insight_person", "")).strip()
    wiki_url = str(payload.get("wiki_url", "")).strip()
    if wiki_url:
        research_run.validate_url(wiki_url, "wiki_url", paper_id)
    with closing(connect(db_path)) as conn:
        with conn:
            cur = conn.execute(
                """
                UPDATE papers
                SET insight_person = ?, wiki_url = ?, updated_at = ?
                WHERE id = ?
                """,
                (insight_person, wiki_url, now_iso(), paper_id),
            )
            rowcount = cur.rowcount
    if rowcount == 0:
        raise research_run.ValidationError(f"{paper_id}: paper_id not found")
    return {"ok": True, "paper_id": paper_id}


def get_paper(db_path: Path, paper_id: str) -> dict | None:
    with closing(connect(db_path)) as conn:
        row = conn.execute(
            f"SELECT {', '.join(PAPER_COLUMNS)} FROM papers WHERE id = ?",
            (paper_id,),
        ).fetchone()
    if row is None:
        return None
    return _attach_row(dict(row))


def update_detail(db_path: Path, payload: dict) -> dict:
    paper_id = str(payload.get("paper_id", "")).strip()
    if not paper_id:
        raise research_run.ValidationError("paper_id is required")
    detail = str(payload.get("detail", ""))
    with closing(connect(db_path)) as conn:
        with conn:
            cur = conn.execute(
                "UPDATE papers SET detail = ?, updated_at = ? WHERE id = ?",
                (detail, now_iso(), paper_id),
            )
            rowcount = cur.rowcount
    if rowcount == 0:
        raise research_run.ValidationError(f"{paper_id}: paper_id not found")
    return {"ok": True, "paper_id": paper_id}
