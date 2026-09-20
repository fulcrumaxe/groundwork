"""Undo last review (I-224): misclick recovery within 60 seconds.

undo() restores the card's scheduling fields and the concept's
mastery from the snapshot submit_review stores on every review row,
then deletes that row. Outside the window (or with no reviews) it
refuses honestly instead of half-restoring.
"""
from __future__ import annotations

from datetime import timedelta
import html

from . import db as dbmod
from . import sched as schedmod

UNDO_WINDOW_SECONDS = 60


def latest(db_path: str) -> dict | None:
    """Newest review with its card + concept, or None when empty."""
    con = dbmod.connect(db_path)
    try:
        return con.execute(
            "SELECT reviews.*, cards.concept_id FROM reviews"
            " JOIN cards ON cards.id = reviews.card_id"
            " ORDER BY reviews.id DESC LIMIT 1").fetchone()
    finally:
        con.close()


def undoable(db_path: str) -> dict | None:
    """Newest review when it is still inside the undo window."""
    row = latest(db_path)
    if row is None:
        return None
    try:
        stamped = schedmod.parse_iso(row["reviewed_at"] or "")
    except ValueError:
        return None
    age = (schedmod.utcnow() - stamped).total_seconds()
    if age < 0 or age > UNDO_WINDOW_SECONDS:
        return None
    return dict(row)


def undo(db_path: str) -> dict:
    """Restore pre-review state and drop the review row."""
    row = undoable(db_path)
    if row is None:
        return {"error": "nothing to undo (older than 60 seconds or empty)"}
    con = dbmod.connect(db_path)
    try:
        con.execute(
            "UPDATE cards SET stability=?, difficulty=?, retrievability=?,"
            " due=?, lapses=? WHERE id=?",
            (row["prev_stability"], row["prev_difficulty"],
             row["prev_retrievability"], row["prev_due"] or None,
             row["prev_lapses"], row["card_id"]))
        con.execute("UPDATE concepts SET mastery=? WHERE id=?",
                    (row["prev_mastery"], row["concept_id"]))
        con.execute("DELETE FROM reviews WHERE id=?", (row["id"],))
        con.commit()
    finally:
        con.close()
    return {"undone_review": row["id"], "card_id": row["card_id"]}


def section_html(db_path: str) -> str:
    """Undo form for the newest review, or the calm empty state."""
    row = latest(db_path)
    if row is None:
        return ("<h2 id='undo'>Undo last review</h2>"
                "<p>No reviews yet — nothing to undo.</p>")
    if undoable(db_path) is None:
        return ("<h2 id='undo'>Undo last review</h2>"
                "<p>The last review is older than 60 seconds — it stands.</p>")
    return (
        f"<h2 id='undo'>Undo last review</h2>"
        f"<p>Misclick? Undo grade {row['grade']}/5 "
        f"(review #{row['id']}) — restores scheduling, drops the row.</p>"
        f"<form method='post' action='/reviews/undo'>"
        f"<button>Undo review #{row['id']}</button></form>")
