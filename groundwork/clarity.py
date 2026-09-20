"""Lesson clarity ratings (I-114): learners rate, authors learn.

record() validates concept + score; summaries() batches averages for a
module page; block_html() renders the average with a 1–5 rating form.
"""
from __future__ import annotations

import html

from . import db as dbmod


def record(db_path: str, concept_id: str, score: int) -> dict:
    """Store one clarity vote; errors stay explicit, never silent."""
    try:
        score_i = int(score)
    except (TypeError, ValueError):
        return {"error": "score must be 1–5"}
    if score_i not in (1, 2, 3, 4, 5):
        return {"error": "score must be 1–5"}
    con = dbmod.connect(db_path)
    try:
        me = con.execute("SELECT concepts.module_id AS mid FROM concepts"
                         " WHERE id=?", (concept_id,)).fetchone()
        if me is None:
            return {"error": "unknown concept"}
        con.execute("INSERT INTO clarity_ratings(concept_id, score)"
                    " VALUES(?, ?)", (concept_id, score_i))
        con.commit()
        return {"rating_id": con.execute(
            "SELECT last_insert_rowid()").fetchone()[0],
            "module_id": me["mid"]}
    finally:
        con.close()


def summaries(db_path: str, cids: list) -> dict:
    """{concept_id: (avg, n)} for a module's concepts in one query."""
    out = {c: (0.0, 0) for c in cids}
    if not cids:
        return out
    con = dbmod.connect(db_path)
    try:
        rows = con.execute(
            "SELECT concept_id, AVG(score) AS avg, COUNT(*) AS n"
            " FROM clarity_ratings"
            f" WHERE concept_id IN ({','.join('?' * len(cids))})"
            " GROUP BY concept_id", cids).fetchall()
    finally:
        con.close()
    for r in rows:
        out[r["concept_id"]] = (r["avg"] or 0.0, r["n"] or 0)
    return out


def block_html(cid: str, avg: float, n: int, origin: str,
               anchor: bool = False) -> str:
    """Average clarity plus the 1–5 vote form for one lesson."""
    mark = " id='clarity'" if anchor else ""
    label = (f"Clarity {avg:.1f}/5 from {n} vote{'s' if n != 1 else ''}"
             if n else "No clarity votes yet — yours teaches the author")
    opts = "".join(
        f"<button name='score' value='{s}'>{s}</button>" for s in (1, 2, 3, 4, 5))
    return (
        f"<p{mark}><small>{html.escape(label)}</small></p>"
        f"<form method='post' action='/concepts/{html.escape(cid)}/rate'>"
        f"<input type='hidden' name='origin' value='{html.escape(origin)}'>"
        f"{opts}</form>")
