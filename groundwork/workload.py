"""Workload forecast: reviews due per day for the next 30 days (I-204).

Buckets the due timestamps the scheduler already stores — no simulation,
no new state. The History page renders the graph; learners see busy days
before they arrive.
"""
from __future__ import annotations

import html
from datetime import timedelta

from . import db as dbmod
from . import sched as schedmod

HORIZON_DAYS = 30


def buckets(db_path: str, days: int = HORIZON_DAYS) -> list[tuple[str, int]]:
    """(date, due-count) for the next `days` days, zeros included."""
    now = schedmod.utcnow()
    end = now + timedelta(days=days)
    con = dbmod.connect(db_path)
    try:
        rows = con.execute(
            "SELECT substr(due, 1, 10) AS d, COUNT(*) AS n FROM cards"
            " WHERE stale = 0 AND due <= ? GROUP BY d",
            (schedmod.iso(end),)).fetchall()
        have = {r["d"]: r["n"] for r in rows}
    finally:
        con.close()
    out = []
    for i in range(days):
        day = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        out.append((day, have.get(day, 0)))
    return out


def section_html(db_path: str) -> str:
    """Workload graph block with a stable tour anchor."""
    rows = buckets(db_path)
    peak = max((n for _, n in rows), default=0)
    cells = "".join(
        f"<tr><td>{d}</td><td>{n}</td>"
        f"<td>{'▇' * min(n, 20) if n else '·'}</td></tr>"
        for d, n in rows)
    return ("<h2 id='workload'>Workload forecast</h2>"
            f"<p><small>Reviews due per day, next {HORIZON_DAYS} days "
            f"(peak {peak}).</small></p>"
            "<table class='log'><tr><th>Day</th><th>Due</th>"
            f"<th></th></tr>{cells}</table>")
