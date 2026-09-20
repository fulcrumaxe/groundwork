"""Serendipity cards (F-137): an adjacent concept you might love.

Picks a non-due concept from the same module as the head of the
queue — adjacent to current work, clearly labeled as a bonus wander,
never a duty. Always renders so the tour anchor never moves.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import lessons as lesmod
from . import sched as schedmod


def pick(db_path: str) -> dict | None:
    """One adjacent non-due concept, or None when the well is dry."""
    now = schedmod.iso(schedmod.utcnow())
    con = dbmod.connect(db_path)
    try:
        head = con.execute(
            "SELECT cards.concept_id, concepts.module_id AS mid FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE cards.due <= ? AND cards.stale = 0"
            " ORDER BY cards.due LIMIT 1", (now,)).fetchone()
        if head is None:
            return None
        due_ids = [r[0] for r in con.execute(
            "SELECT concept_id FROM cards WHERE due <= ? AND stale = 0",
            (now,)).fetchall()]
        params: list = [head["mid"]]
        filt = ""
        if due_ids:
            filt = f" AND concepts.id NOT IN ({','.join('?' * len(due_ids))})"
            params += due_ids
        row = con.execute(
            "SELECT concepts.id AS cid, concepts.name AS concept,"
            " modules.task_summary AS summary FROM concepts"
            " JOIN modules ON modules.id = concepts.module_id"
            " WHERE concepts.module_id = ?" + filt +
            " ORDER BY concepts.rowid LIMIT 1", params).fetchone()
        if row is None:
            return None
        return {"cid": row["cid"], "concept": row["concept"] or "",
                "mid": head["mid"], "summary": row["summary"] or ""}
    finally:
        con.close()


def section_html(db_path: str) -> str:
    """Bonus wander, labeled as what it is."""
    cand = pick(db_path)
    if cand is None:
        return ("<section id='serendipity'><h2>Serendipity</h2>"
                "<p>Nothing adjacent right now — the whole neighborhood "
                "is already in your queue.</p></section>")
    node = cand["cid"].split(":", 1)[-1]
    return (
        f"<section id='serendipity'><h2>Serendipity</h2>"
        f"<p>Bonus, not duty: <a href='/modules/{cand['mid']}"
        f"#lesson-{lesmod.slug(node)}'>"
        f"{html.escape(cand['concept'] or node)}</a> "
        f"(in {html.escape(cand['summary'] or cand['mid'])}) sits next to "
        f"what you are practicing — wander over if you are curious.</p>"
        f"</section>")
