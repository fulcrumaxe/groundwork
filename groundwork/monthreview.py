"""Month in review (I-244): concepts owned, accuracy trend, effort.

Pure renderer over a database path — the History page calls
section_html after the week ritual. Effort is reported as attempts
across active days (no fake minutes: Groundwork never times you).
Always renders so the tour anchor never moves.
"""
from __future__ import annotations

from datetime import timedelta

from . import db as dbmod
from . import ownership as ownmod
from . import sched as schedmod


def _window(con, days_ago: int, span: int) -> tuple:
    """(attempts, passed, active days) for [now-days_ago-span, now-days_ago)."""
    lo = (schedmod.utcnow() - timedelta(days=days_ago + span)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    hi = (schedmod.utcnow() - timedelta(days=days_ago)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    return con.execute(
        "SELECT COUNT(*) AS n,"
        " SUM(CASE WHEN grade >= 4 THEN 1 ELSE 0 END) AS ok,"
        " COUNT(DISTINCT substr(reviewed_at, 1, 10)) AS days"
        " FROM reviews WHERE reviewed_at >= ? AND reviewed_at <= ?",
        (lo, hi)).fetchone()


def section_html(db_path: str) -> str:
    """Last 30 days: owned concepts, accuracy trend, effort."""
    con = dbmod.connect(db_path)
    try:
        recent = _window(con, 0, 30)
        halves = (_window(con, 15, 15), _window(con, 0, 15))
        owned_n = 0
        for (mid,) in con.execute("SELECT id FROM modules").fetchall():
            owned_n += sum(1 for _, o in ownmod.owned_map(con, mid).values()
                           if o)
    finally:
        con.close()
    n, ok, days = recent["n"] or 0, recent["ok"] or 0, recent["days"] or 0
    if not n:
        return ("<h2 id='month'>This month</h2><p>No attempts in the last "
                "30 days — the queue keeps no grudges.</p>")
    acc = round(100 * ok / n)
    trends = []
    for w in halves:
        wn = w["n"] or 0
        trends.append(f"{round(100 * (w['ok'] or 0) / wn)}%" if wn else "—")
    return (
        f"<h2 id='month'>This month</h2><p>{n} attempts across {days} "
        f"active day{'s' if days != 1 else ''} · {ok} passed ({acc}%) · "
        f"{owned_n} concept{'s' if owned_n != 1 else ''} owned. "
        f"Accuracy trend: {trends[0]} → {trends[1]} "
        f"(days −30…−15 vs −15…today).</p>")
