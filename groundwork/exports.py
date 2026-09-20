"""Study-data exports: Anki TSV, review-log CSV, RSS feed, personal JSON.

Pure renderers over a database path — no HTTP, no page chrome.
The web Handler delegates here so export logic never lives in web.py.
"""
from __future__ import annotations

import csv
import html
import io
import json
import re
from email.utils import formatdate

from . import db as dbmod
from . import sched as schedmod


def anki_tsv(db_path: str) -> str:
    """All cards as Anki plain-text import (front\\tback\\ttags)."""
    con = dbmod.connect(db_path)
    try:
        rows = con.execute(
            "SELECT cards.front, cards.back, modules.task_summary,"
            " modules.id FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " JOIN modules ON modules.id = concepts.module_id"
            " ORDER BY modules.created_at, cards.id").fetchall()
    finally:
        con.close()
    lines = []
    for r in rows:
        fields = []
        for v in (r["front"] or "", r["back"] or ""):
            v = html.escape(v, quote=False)
            fields.append(v.replace("\t", " ").replace("\r\n", "<br>")
                          .replace("\n", "<br>"))
        tag = re.sub(r"\s+", "-", (r["task_summary"] or r["id"] or "")
                     .strip().lower())[:40]
        lines.append("\t".join(fields + [tag]))
    return "\n".join(lines) + ("\n" if lines else "")


def reviews_csv(db_path: str) -> str:
    """Review log as CSV for personal analysis (I-231)."""
    con = dbmod.connect(db_path)
    try:
        rows = con.execute(
            "SELECT reviews.reviewed_at, concepts.name AS concept,"
            " modules.task_summary AS summary, reviews.grade,"
            " reviews.confidence, reviews.submission"
            " FROM reviews JOIN cards ON cards.id = reviews.card_id"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " JOIN modules ON modules.id = concepts.module_id"
            " ORDER BY reviews.id").fetchall()
    finally:
        con.close()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["reviewed_at", "concept", "module", "grade",
                "confidence", "pass", "submission"])
    for r in rows:
        w.writerow([r["reviewed_at"] or "", r["concept"] or "",
                    r["summary"] or "", r["grade"],
                    r["confidence"],
                    "yes" if (r["grade"] or 0) >= 4 else "no",
                    r["submission"] or ""])
    return buf.getvalue()


def feed_xml(db_path: str, base_url: str) -> str:
    """RSS 2.0 feed of learning modules for external readers."""
    con = dbmod.connect(db_path)
    try:
        mods = con.execute(
            "SELECT modules.id, modules.task_summary, modules.created_at,"
            " COUNT(DISTINCT concepts.id) AS n FROM modules"
            " LEFT JOIN concepts ON concepts.id LIKE modules.id || ':%'"
            " GROUP BY modules.id ORDER BY modules.created_at DESC"
            " LIMIT 50").fetchall()
    finally:
        con.close()
    items = []
    for m in mods:
        try:
            stamp = schedmod.parse_iso(m["created_at"] or "").timestamp()
            pub = formatdate(stamp, usegmt=True)
        except Exception:  # noqa: BLE001 — raw date still renders
            pub = m["created_at"] or ""
        link = f"{base_url}/modules/{m['id']}"
        items.append(
            f"<item><title>{html.escape(m['task_summary'] or m['id'])}</title>"
            f"<link>{html.escape(link)}</link>"
            f"<guid>{html.escape(link)}</guid>"
            f"<pubDate>{html.escape(pub)}</pubDate>"
            f"<description>{m['n'] or 0} concepts</description></item>")
    return ("<?xml version='1.0' encoding='UTF-8'?>"
            "<rss version='2.0'><channel>"
            "<title>Groundwork modules</title>"
            f"<link>{html.escape(base_url)}/modules</link>"
            "<description>Every agent session as a lesson.</description>"
            + "".join(items) + "</channel></rss>")


def _dump(con, table: str, cols: str) -> list:
    """Whole table as plain dicts; missing tables read as empty."""
    try:
        return [dict(r) for r in con.execute(
            f"SELECT {cols} FROM {table} ORDER BY rowid").fetchall()]
    except Exception:  # noqa: BLE001 — older DBs predate the table
        return []


def personal_json(db_path: str) -> str:
    """Everything about you in one JSON (F-292): portable, private."""
    con = dbmod.connect(db_path)
    try:
        data = {
            "modules": _dump(con, "modules",
                             "id, repo, task_summary, created_at"),
            "concepts": _dump(con, "concepts",
                              "id, module_id, name, kind, mastery"),
            "cards": _dump(con, "cards",
                           "id, concept_id, exercise_type, stability,"
                           " difficulty, due, lapses, stale"),
            "reviews": _dump(con, "reviews",
                             "card_id, grade, confidence, reviewed_at,"
                             " submission"),
            "decisions": _dump(con, "decisions",
                               "repo, symbol, chosen, rejected, reason,"
                               " created_at"),
            "holes": _dump(con, "holes",
                           "repo, file, line, spec, status, created_at"),
            "disputes": _dump(con, "disputes",
                              "card_id, reason, status, created_at"),
            "clarity_ratings": _dump(con, "clarity_ratings",
                                     "concept_id, score, created_at"),
            "known_skips": _dump(con, "known_skips",
                                 "concept_id, verify_due, created_at"),
            "journal": _dump(con, "journal_entries",
                             "created_day, prompt, body, created_at"),
            "tool_calls": _dump(con, "tool_calls",
                                "method, ok, ms, created_at"),
        }
    finally:
        con.close()
    return json.dumps(data, indent=1, sort_keys=True)
