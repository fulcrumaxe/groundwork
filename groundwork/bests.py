"""Personal bests (F-101): accuracy, depth and dedication — never streaks.

Strongest memory (highest stability), most practiced concept, and
sharpest skill (best accuracy with 3+ attempts). Personal only, calm
by design. Always renders so the tour anchor never moves.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import exercises as exmod


def bests(db_path: str) -> dict:
    """Strongest memory, most practiced concept, sharpest skill."""
    con = dbmod.connect(db_path)
    try:
        strong = con.execute(
            "SELECT concepts.name AS concept, cards.stability FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " ORDER BY cards.stability DESC LIMIT 1").fetchone()
        practiced = con.execute(
            "SELECT concepts.name AS concept, COUNT(*) AS n FROM reviews"
            " JOIN cards ON cards.id = reviews.card_id"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " GROUP BY concepts.id ORDER BY n DESC LIMIT 1").fetchone()
        rows = con.execute(
            "SELECT cards.exercise_type, reviews.grade FROM reviews"
            " JOIN cards ON cards.id = reviews.card_id").fetchall()
    finally:
        con.close()
    sharp = None
    by_bloom: dict[str, list] = {}
    for etype, grade in rows:
        try:
            bloom = exmod.TYPES[int(etype)][1]
        except (ValueError, KeyError, TypeError):
            bloom = "other"
        by_bloom.setdefault(bloom, []).append(grade or 0)
    for bloom in sorted(by_bloom):
        rs = by_bloom[bloom]
        if len(rs) >= 3:
            acc = sum(1 for g in rs if g >= 4) / len(rs)
            if sharp is None or acc > sharp[1]:
                sharp = (bloom, acc, len(rs))
    return {"strong": dict(strong) if strong else None,
            "practiced": dict(practiced) if practiced else None,
            "sharp": sharp}


def section_html(db_path: str) -> str:
    """History section: your bests, framed fondly."""
    b = bests(db_path)
    if b["strong"] is not None:
        mem = (f"Strongest memory: "
               f"{html.escape(b['strong']['concept'] or '')} "
               f"({(b['strong']['stability'] or 0):.0f}-day stability).")
    else:
        mem = "Strongest memory: none yet — every review builds one."
    if b["practiced"] is not None:
        prac = (f"Most practiced: "
                f"{html.escape(b['practiced']['concept'] or '')} "
                f"({b['practiced']['n']} attempts).")
    else:
        prac = "Most practiced: none yet."
    if b["sharp"] is not None:
        bloom, acc, n = b["sharp"]
        skill = (f"Sharpest skill: {html.escape(bloom)} "
                 f"({acc:.0%} over {n} attempts).")
    else:
        skill = "Sharpest skill: needs 3+ attempts on one skill to judge."
    return (f"<h2 id='bests'>Personal bests</h2>"
            f"<p>{mem} {prac} {skill}</p>")
