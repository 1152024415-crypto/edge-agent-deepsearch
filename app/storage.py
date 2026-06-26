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
    "score_vendor",
    "score_contribution",
    "score_quality",
    "score_recency",
    "score_reason",
    "source_type",
    "is_major_vendor_official",
    "category",
    "keywords",
    "insight_person",
    "wiki_url",
    "authors",
    "vendors",
    "venue",
    "recommendation",
    "detail",
    "updated_at",
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
                    score_vendor INTEGER,
                    score_contribution INTEGER,
                    score_quality INTEGER,
                    score_recency INTEGER,
                    score_reason TEXT,
                    source_type TEXT NOT NULL,
                    is_major_vendor_official INTEGER NOT NULL DEFAULT 0,
                    category TEXT,
                    keywords TEXT,
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
            for field in ("score_relevance", "score_vendor", "score_contribution", "score_quality", "score_recency"):
                if field not in columns:
                    conn.execute(f"ALTER TABLE papers ADD COLUMN {field} INTEGER")
            if "score_reason" not in columns:
                conn.execute("ALTER TABLE papers ADD COLUMN score_reason TEXT")
            if "is_major_vendor_official" not in columns:
                conn.execute("ALTER TABLE papers ADD COLUMN is_major_vendor_official INTEGER NOT NULL DEFAULT 0")
            if "category" not in columns:
                conn.execute("ALTER TABLE papers ADD COLUMN category TEXT")
            if "keywords" not in columns:
                conn.execute("ALTER TABLE papers ADD COLUMN keywords TEXT")
            if "detail" not in columns:
                conn.execute("ALTER TABLE papers ADD COLUMN detail TEXT")


def upsert_run(db_path: Path, payload: dict) -> dict:
    normalized = research_run.validate_payload(payload)
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
                values["is_major_vendor_official"] = int(bool(values.get("is_major_vendor_official")))
                values["keywords"] = json.dumps(values.get("keywords", []), ensure_ascii=False)
                conn.execute(
                    """
                    INSERT INTO papers (
                        id, run_id, title, abstract, effects, mechanism, paper_url, date, score,
                        score_relevance, score_vendor, score_contribution, score_quality, score_recency,
                        score_reason, source_type, is_major_vendor_official, insight_person,
                        category, keywords, wiki_url, authors, vendors, venue, recommendation, updated_at
                    )
                    VALUES (
                        :id, :run_id, :title, :abstract, :effects, :mechanism, :paper_url, :date,
                        :score, :score_relevance, :score_vendor, :score_contribution, :score_quality,
                        :score_recency, :score_reason, :source_type, :is_major_vendor_official,
                        :insight_person, :category, :keywords, :wiki_url, :authors, :vendors, :venue,
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
                        score_vendor = excluded.score_vendor,
                        score_contribution = excluded.score_contribution,
                        score_quality = excluded.score_quality,
                        score_recency = excluded.score_recency,
                        score_reason = excluded.score_reason,
                        source_type = excluded.source_type,
                        is_major_vendor_official = excluded.is_major_vendor_official,
                        category = excluded.category,
                        keywords = excluded.keywords,
                        authors = excluded.authors,
                        vendors = excluded.vendors,
                        venue = excluded.venue,
                        recommendation = excluded.recommendation,
                        updated_at = excluded.updated_at
                    """,
                    values,
                )
    return {"ok": True, "run_id": normalized["run_id"], "accepted": len(normalized["papers"])}


def list_papers(db_path: Path, sort: str = "score") -> list[dict]:
    order_by = (
        "is_major_vendor_official DESC, score DESC, date DESC, title ASC"
        if sort != "date"
        else "is_major_vendor_official DESC, date DESC, score DESC, title ASC"
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
    papers = [dict(row) for row in rows]
    for paper in papers:
        paper["is_major_vendor_official"] = bool(paper.get("is_major_vendor_official"))
        try:
            keywords = json.loads(paper.get("keywords") or "[]")
        except json.JSONDecodeError:
            keywords = []
        paper["keywords"] = keywords if isinstance(keywords, list) else []
    return papers


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
    paper = dict(row)
    paper["is_major_vendor_official"] = bool(paper.get("is_major_vendor_official"))
    try:
        keywords = json.loads(paper.get("keywords") or "[]")
    except json.JSONDecodeError:
        keywords = []
    paper["keywords"] = keywords if isinstance(keywords, list) else []
    return paper


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
