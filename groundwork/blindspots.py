"""Blind spots (F-184): documentation coverage from owned maps.

Lists the lowest-mastery concepts — what nobody understands yet —
with links to their lessons, so study time goes where it matters.
Always renders so the tour anchor never moves.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import lessons as lesmod

LIMIT = 10


def section_html(db_path: str) -> str:
    """Bottom-mastery concepts with lesson links."""
    con = dbmod.connect(db_path)
    try:
        rows = con.execute(
            "SELECT concepts.id AS cid, concepts.name AS concept,"
            " concepts.mastery AS mastery, concepts.module_id AS mid,"
            " modules.task_summary AS summary FROM concepts"
            " JOIN modules ON modules.id = concepts.module_id"
            " ORDER BY concepts.mastery ASC, concepts.rowid LIMIT ?",
            (LIMIT,)).fetchall()
    finally:
        con.close()
    if not rows:
        return ("<h2 id='status-blindspots'>Blind spots</h2>"
                "<p>No concepts yet — blind spots appear with modules.</p>")
    items = []
    for r in rows:
        node = r["cid"].split(":", 1)[-1]
        pct = round(100 * (r["mastery"] or 0.0))
        items.append(
            f"<li><a href='/modules/{r['mid']}#lesson-{lesmod.slug(node)}'>"
            f"{html.escape(r['concept'] or node)}</a> "
            f"<small>({pct}% · {html.escape(r['summary'] or r['mid'])})</small></li>")
    return ("<h2 id='status-blindspots'>Blind spots</h2>"
            "<p>Lowest-mastery concepts — what nobody understands yet.</p>"
            "<ul>" + "".join(items) + "</ul>")
