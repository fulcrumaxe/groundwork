"""Shared read queries: lessons, attempt counts, per-card history.

Taken out of the web Handler so the Due and module pages share one
implementation without living in web.py.
"""
from __future__ import annotations

import json


def stored_lessons(con, card_ids: list[str]) -> dict:
    """(lesson dict, mastery) per card from lessons stored at creation."""
    if not card_ids:
        return {}
    rows = con.execute(
        "SELECT cards.id AS card, cards.concept_id AS cid, modules.lessons,"
        " concepts.mastery AS mastery"
        " FROM cards JOIN concepts ON concepts.id = cards.concept_id"
        " JOIN modules ON modules.id = concepts.module_id"
        f" WHERE cards.id IN ({','.join('?' * len(card_ids))})",
        card_ids).fetchall()
    out = {}
    for r in rows:
        try:
            lessons = {L["concept_id"]: L for L in json.loads(r["lessons"] or "[]")}
        except ValueError:
            continue
        node = r["cid"].split(":", 1)[1] if ":" in r["cid"] else r["cid"]
        if node in lessons:
            out[r["card"]] = (lessons[node], r["mastery"] or 0.0)
    return out


def attempts(con, card_ids: list[str]) -> dict:
    """Attempt counts per card id."""
    if not card_ids:
        return {}
    rows = con.execute(
        "SELECT card_id, COUNT(*) AS n FROM reviews"
        f" WHERE card_id IN ({','.join('?' * len(card_ids))})"
        " GROUP BY card_id", card_ids).fetchall()
    return {r["card_id"]: r["n"] for r in rows}


def cold_rows(con) -> list:
    """Concept rows for cold-attempt sessions: id, module, name, mastery."""
    rows = con.execute(
        "SELECT id, module_id, name, mastery FROM concepts").fetchall()
    return [{"id": r["id"], "module_id": r["module_id"],
             "name": r["name"], "mastery": r["mastery"] or 0.0}
            for r in rows]


def history_by_card(con, mid: str) -> dict:
    """Past reviews per card for one module, newest first."""
    try:
        rows = con.execute(
            "SELECT reviews.card_id, reviews.grade, reviews.confidence,"
            " reviews.reviewed_at, reviews.submission FROM reviews"
            " JOIN cards ON cards.id = reviews.card_id"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=? ORDER BY reviews.id DESC",
            (mid,)).fetchall()
    except Exception:  # noqa: BLE001 — pre-migration DBs lack submission
        rows = con.execute(
            "SELECT reviews.card_id, reviews.grade, reviews.confidence,"
            " reviews.reviewed_at FROM reviews"
            " JOIN cards ON cards.id = reviews.card_id"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=? ORDER BY reviews.id DESC",
            (mid,)).fetchall()
        rows = [dict(r, submission="") for r in rows]
        out = {}
        for r in rows:
            out.setdefault(r["card_id"], []).append(r)
        return out
    out = {}
    for r in rows:
        out.setdefault(r["card_id"], []).append(dict(r))
    return out
