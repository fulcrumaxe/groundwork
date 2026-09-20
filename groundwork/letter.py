"""Weekly letter to self (F-106): an auto-drafted progress note.

Private prose from real numbers — this week's attempts, owned count,
the weakest skill by accuracy, and one concrete next step. No streaks,
no shame, one gentle suggestion.
"""
from __future__ import annotations

from datetime import timedelta
import html

from . import db as dbmod
from . import exercises as exmod
from . import lessons as lesmod
from . import ownership as ownmod
from . import sched as schedmod


def draft(db_path: str) -> str:
    """The letter body as plain text from this week's numbers."""
    since = (schedmod.utcnow() - timedelta(days=7)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    con = dbmod.connect(db_path)
    try:
        week = con.execute(
            "SELECT COUNT(*) AS n,"
            " SUM(CASE WHEN grade >= 4 THEN 1 ELSE 0 END) AS ok,"
            " COUNT(DISTINCT substr(reviewed_at, 1, 10)) AS days"
            " FROM reviews WHERE reviewed_at >= ?", (since,)).fetchone()
        rows = con.execute(
            "SELECT cards.exercise_type, reviews.grade FROM reviews"
            " JOIN cards ON cards.id = reviews.card_id"
            " WHERE reviews.reviewed_at >= ?", (since,)).fetchall()
        owned_n = 0
        for (mid,) in con.execute("SELECT id FROM modules").fetchall():
            owned_n += sum(1 for _, o in ownmod.owned_map(con, mid).values()
                           if o)
        first = con.execute(
            "SELECT cards.concept_id, concepts.name AS concept,"
            " concepts.module_id AS mid FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE cards.due <= ? AND cards.stale = 0"
            " ORDER BY cards.due LIMIT 1",
            (schedmod.iso(schedmod.utcnow()),)).fetchone()
    finally:
        con.close()
    n, ok, days = week["n"] or 0, week["ok"] or 0, week["days"] or 0
    if not n:
        return ("Dear learner, you practiced nothing this week — and that "
                "is information, not failure. One card today restarts the "
                "loop; the queue keeps no grudges.")
    by_bloom: dict[str, list] = {}
    for etype, grade in rows:
        try:
            bloom = exmod.TYPES[int(etype)][1]
        except (ValueError, KeyError, TypeError):
            bloom = "other"
        by_bloom.setdefault(bloom, []).append(grade or 0)
    weak = None
    for bloom in sorted(by_bloom):
        rs = by_bloom[bloom]
        if len(rs) >= 2:
            acc = sum(1 for g in rs if g >= 4) / len(rs)
            if weak is None or acc < weak[1]:
                weak = (bloom, acc)
    acc_all = round(100 * ok / n)
    lines = [f"Dear learner, this week you made {n} attempts across "
             f"{days} active day{'s' if days != 1 else ''}, passing "
             f"{ok} ({acc_all}%). You own {owned_n} concept"
             f"{'s' if owned_n != 1 else ''} in total."]
    if weak is not None:
        lines.append(f"Your tender spot is {weak[0]} "
                     f"({weak[1]:.0%} this week) — not a verdict, a compass.")
    if first is not None:
        node = first["concept_id"].split(":", 1)[-1]
        lines.append(f"Next: {first['concept'] or node} "
                     f"(/modules/{first['mid']}#lesson-{lesmod.slug(node)}).")
    lines.append("Keep going — gently.")
    return " ".join(lines)


def section_html(db_path: str) -> str:
    """Status section: the letter, private by design."""
    return (f"<h2 id='status-letter'>Letter to self</h2>"
            f"<p>{html.escape(draft(db_path))}</p>")
