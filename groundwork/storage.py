"""Storage meter: where the learning data lives and how big (I-238).

Self-hosters hold real databases — this section says how big the file
is and how rows split across modules, so growth never surprises.
"""
from __future__ import annotations

import html
from pathlib import Path

from . import db as dbmod


def _human(n: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(max(0, n))
    for u in units:
        if size < 1024 or u == units[-1]:
            return f"{size:.0f} {u}" if u == "B" else f"{size:.1f} {u}"
        size /= 1024
    return f"{size:.1f} GB"


def usage(db_path: str) -> dict:
    """File size plus per-module row counts."""
    con = dbmod.connect(db_path)
    try:
        mods = con.execute(
            "SELECT id, task_summary FROM modules ORDER BY created_at DESC"
        ).fetchall()
        rows = []
        for m in mods:
            concepts = con.execute(
                "SELECT COUNT(*) FROM concepts WHERE module_id=?",
                (m["id"],)).fetchone()[0]
            cards = con.execute(
                "SELECT COUNT(*) FROM cards JOIN concepts"
                " ON concepts.id = cards.concept_id"
                " WHERE concepts.module_id=?", (m["id"],)).fetchone()[0]
            reviews = con.execute(
                "SELECT COUNT(*) FROM reviews JOIN cards"
                " ON cards.id = reviews.card_id JOIN concepts"
                " ON concepts.id = cards.concept_id"
                " WHERE concepts.module_id=?", (m["id"],)).fetchone()[0]
            rows.append({"id": m["id"],
                         "task_summary": m["task_summary"] or "",
                         "concepts": concepts, "cards": cards,
                         "reviews": reviews})
        disputes = con.execute("SELECT COUNT(*) FROM disputes").fetchone()[0]
    finally:
        con.close()
    try:
        size = Path(db_path).stat().st_size
    except OSError:
        size = 0
    return {"bytes": size, "human": _human(size), "modules": rows,
            "disputes": disputes}


def section_html(db_path: str) -> str:
    """Storage section with a stable tour anchor."""
    info = usage(db_path)
    cells = "".join(
        f"<tr><td><a href='/modules/{html.escape(m['id'])}'>"
        f"{html.escape(m['task_summary'] or m['id'])}</a></td>"
        f"<td>{m['concepts']}</td><td>{m['cards']}</td>"
        f"<td>{m['reviews']}</td></tr>" for m in info["modules"])
    return ("<h2 id='status-storage'>Storage</h2>"
            f"<p><small>Database file: {html.escape(info['human'])} · "
            f"{info['disputes']} dispute(s) on record.</small></p>"
            "<table class='log'><tr><th>Module</th><th>Concepts</th>"
            f"<th>Cards</th><th>Reviews</th></tr>{cells}</table>")
