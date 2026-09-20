"""Daily digest (I-242): today's queue at a glance, no email needed.

Pure renderer over a database path — the web Handler calls
section_html at the top of Due. Always renders (with a calm
all-clear when nothing is due) so the tour anchor never moves.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import lessons as lesmod
from . import sched as schedmod


def section_html(db_path: str) -> str:
    """Today: due now, new cards, due tomorrow, suggested start."""
    now = schedmod.iso(schedmod.utcnow())
    con = dbmod.connect(db_path)
    try:
        due_now = con.execute(
            "SELECT COUNT(*) FROM cards WHERE due <= ? AND stale = 0",
            (now,)).fetchone()[0]
        new = con.execute(
            "SELECT COUNT(*) FROM cards WHERE cards.stale = 0 AND NOT EXISTS"
            " (SELECT 1 FROM reviews WHERE reviews.card_id = cards.id)"
            ).fetchone()[0]
        tomorrow = con.execute(
            "SELECT COUNT(*) FROM cards WHERE cards.due > ?"
            " AND cards.due <= datetime(?, '+1 day') AND cards.stale = 0",
            (now, now)).fetchone()[0]
        first = con.execute(
            "SELECT cards.concept_id, concepts.name AS concept,"
            " concepts.module_id AS mid FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE cards.due <= ? AND cards.stale = 0"
            " ORDER BY cards.due LIMIT 1", (now,)).fetchone()
    finally:
        con.close()
    if first is not None:
        node = first["concept_id"].split(":", 1)[-1]
        start = (f"Start with <a href='/modules/{first['mid']}"
                 f"#lesson-{lesmod.slug(node)}'>"
                 f"{html.escape(first['concept'] or node)}</a>.")
    else:
        start = "All clear — nothing due. Browse a module to learn ahead."
    return (
        f"<section id='digest'><h2>Today</h2><p>{due_now} due now · "
        f"{new} new · {tomorrow} more by tomorrow. {start}</p></section>")
