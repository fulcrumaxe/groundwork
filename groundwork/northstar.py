"""North-star dashboard (F-52): delayed accuracy for the learner.

The headline number is pass rate on reviews of mature cards only
(stability at review time of 21+ days) — same-day fluency never
counts. Concepts owned rides alongside as the volume number.
"""
from __future__ import annotations

from . import db as dbmod
from . import ownership as ownmod

MATURE_DAYS = 21.0


def snapshot(db_path: str) -> dict:
    """Delayed accuracy (mature reviews) + owned concepts + attempts."""
    con = dbmod.connect(db_path)
    try:
        try:
            mature = con.execute(
                "SELECT COUNT(*) AS n,"
                " SUM(CASE WHEN grade >= 4 THEN 1 ELSE 0 END) AS ok"
                " FROM reviews WHERE prev_stability >= ?",
                (MATURE_DAYS,)).fetchone()
        except Exception:  # noqa: BLE001 — pre-undo DBs lack the column
            mature = {"n": 0, "ok": 0}
        tries = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        owned_n = 0
        for (mid,) in con.execute("SELECT id FROM modules").fetchall():
            owned_n += sum(1 for _, o in ownmod.owned_map(con, mid).values()
                           if o)
    finally:
        con.close()
    n, ok = mature["n"] or 0, mature["ok"] or 0
    return {"mature_n": n, "delayed_acc": (ok / n if n else None),
            "owned": owned_n, "attempts": tries}


def section_html(db_path: str) -> str:
    """Status section: the learner's north star, honestly footnoted."""
    s = snapshot(db_path)
    if s["delayed_acc"] is None:
        star = (f"No mature recalls yet — delayed accuracy appears once "
                f"you review cards stable {int(MATURE_DAYS)}+ days.")
    else:
        star = (f"Delayed accuracy <b>{s['delayed_acc']:.0%}</b> "
                f"(n={s['mature_n']}) — recalls of cards stable "
                f"{int(MATURE_DAYS)}+ days. Same-day fluency excluded.")
    return (
        f"<h2 id='status-northstar'>North star</h2>"
        f"<p>{s['owned']} concepts owned · {s['attempts']} attempts. "
        f"{star}</p>")
