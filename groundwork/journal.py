"""Metacognition journal (F-68): weekly "what did I misjudge?" prompt.

The prompt is data-driven: the skill with the worst overconfidence gap
(3+ attempts, confidence beating accuracy by 15+ points) becomes the
question. Entries are private markdown-ish text, listed newest first.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import emptyart as emptyartmod
from . import exercises as exmod
from . import sched as schedmod


def week_prompt(db_path: str) -> str:
    """This week's misjudgment question from real calibration data."""
    con = dbmod.connect(db_path)
    try:
        rows = con.execute(
            "SELECT cards.exercise_type, reviews.grade, reviews.confidence"
            " FROM reviews JOIN cards ON cards.id = reviews.card_id"
            " ORDER BY reviews.id DESC LIMIT 500").fetchall()
    finally:
        con.close()
    by_bloom: dict[str, list] = {}
    for etype, grade, conf in rows:
        try:
            bloom = exmod.TYPES[int(etype)][1]
        except (ValueError, KeyError, TypeError):
            bloom = "other"
        by_bloom.setdefault(bloom, []).append((grade, conf))
    worst = None
    for bloom in sorted(by_bloom):
        rs = by_bloom[bloom]
        if len(rs) < 3:
            continue
        acc = sum(1 for g, _ in rs if (g or 0) >= 4) / len(rs)
        avg_conf = sum(((c or 3) - 1) / 4 for _, c in rs) / len(rs)
        if avg_conf - acc >= 0.15 and (worst is None
                                      or avg_conf - acc > worst[1]):
            worst = (bloom, avg_conf - acc, acc, avg_conf)
    if worst is None:
        return ("What surprised you in your practice this week — "
                "a card you were sure about but missed?")
    bloom, _, acc, avg_conf = worst
    return (f"On {bloom} exercises you felt {avg_conf:.0%} confident but "
            f"scored {acc:.0%}. What exactly did you misjudge?")


def save(db_path: str, body: str) -> dict:
    """Store one journal entry under today's prompt."""
    body = (body or "").strip()[:4000]
    if not body:
        return {"error": "empty entry — write a sentence first"}
    prompt = week_prompt(db_path)
    day = schedmod.utcnow().strftime("%Y-%m-%d")
    con = dbmod.connect(db_path)
    try:
        con.execute("INSERT INTO journal_entries(created_day, prompt, body)"
                    " VALUES(?,?,?)", (day, prompt, body))
        con.commit()
    finally:
        con.close()
    return {"entry_day": day}


def entries(db_path: str) -> list:
    """Past entries, newest first."""
    con = dbmod.connect(db_path)
    try:
        return con.execute(
            "SELECT created_day, prompt, body, created_at FROM journal_entries"
            " ORDER BY id DESC LIMIT 52").fetchall()
    finally:
        con.close()


def page_html(db_path: str) -> str:
    """Journal page: this week's prompt, the form, past entries."""
    prompt = week_prompt(db_path)
    past = "".join(
        f"<article><h3>{html.escape(r['created_day'] or '')}</h3>"
        f"<p><small>{html.escape(r['prompt'] or '')}</small></p>"
        f"<p>{html.escape(r['body'] or '')}</p></article>"
        for r in entries(db_path))
    if not past:
        past = (emptyartmod.art_for("journal") +
                "<p>No entries yet — the first honest sentence is the hardest.</p>")
    return (
        f"<div id='journal'><h2>This week's question</h2>"
        f"<p><b>{html.escape(prompt)}</b></p>"
        f"<form method='post' action='/journal'>"
        f"<textarea name='body' rows='4' "
        f"placeholder='What did you misjudge?'></textarea><br>"
        f"<button>Save entry (private)</button></form>"
        f"<h2>Past entries</h2>{past}</div>")
