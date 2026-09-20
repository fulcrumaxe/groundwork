"""Per-module progress reset, behind a confirm page (I-236, I-36).

Resetting deletes a module's reviews, restores fresh scheduling on
every card, and zeroes concept mastery. Modules, concepts, cards, and
lessons are untouched — only personal progress is wiped.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import sched as schedmod


def reset_module(db_path: str, mid: str) -> dict:
    """Wipe one module's progress; unknown modules are refused."""
    con = dbmod.connect(db_path)
    try:
        m = con.execute("SELECT task_summary FROM modules WHERE id=?",
                        (mid,)).fetchone()
        if m is None:
            return {"error": "unknown module"}
        now = schedmod.iso(schedmod.utcnow())
        # Stale flags stay: the code drift they record is still true.
        cards = con.execute(
            "UPDATE cards SET stability=1.0, difficulty=0.5,"
            " retrievability=1.0, due=?, lapses=0"
            " WHERE concept_id IN (SELECT id FROM concepts"
            " WHERE module_id=?)",
            (now, mid)).rowcount
        reviews = con.execute(
            "DELETE FROM reviews WHERE card_id IN (SELECT cards.id"
            " FROM cards JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=?)", (mid,)).rowcount
        con.execute("UPDATE concepts SET mastery=0.0 WHERE module_id=?",
                    (mid,))
        con.commit()
        return {"module_id": mid, "cards_reset": cards,
                "reviews_deleted": reviews}
    finally:
        con.close()


def confirm_html(mid: str, summary: str) -> str:
    """Destructive action behind a confirm page (I-36)."""
    return (
        f"<h2 id='reset-confirm'>Reset this module?</h2>"
        f"<p>Starting <b>{html.escape(summary or mid)}</b> over deletes "
        f"its reviews, restores fresh scheduling, and zeroes mastery. "
        f"Lessons and cards stay.</p>"
        f"<form method='post' action='/modules/{html.escape(mid)}/reset'>"
        f"<button>Yes, reset my progress</button> "
        f"<a class='btn' href='/modules/{html.escape(mid)}'>Keep it</a></form>")


def reset_link_html(mid: str) -> str:
    """Small reset entry point for the module page."""
    return (f"<p id='reset'><small><a href='/modules/{html.escape(mid)}/reset'>"
            f"Reset progress…</a></small></p>")
