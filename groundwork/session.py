"""Session-end summary (I-47/F-session).

Pure helpers over this session's review rows — no DB, no schema
changes. Grade >= 4 counts as correct, matching history/monthreview
conventions. Always renders so the tour anchor never moves.
"""
from __future__ import annotations

import html

PASS_GRADE = 4


def summarize(reviews) -> dict:
    """Summarize one session's review rows.

    Each row is a dict with grade (0-5) and optional due (ISO
    next-due str), or a (grade, due) / (grade,) tuple. Non-row
    entries are ignored.
    """
    answered = 0
    correct = 0
    earliest = ""
    for row in reviews or []:
        grade = None
        due = ""
        if isinstance(row, dict):
            grade, due = row.get("grade"), row.get("due") or ""
        elif isinstance(row, (list, tuple)) and row:
            grade = row[0]
            due = row[1] if len(row) > 1 else ""
        try:
            g = int(grade)
        except (TypeError, ValueError):
            continue
        answered += 1
        if g >= PASS_GRADE:
            correct += 1
        if isinstance(due, str) and due and (not earliest or due < earliest):
            earliest = due
    accuracy = round(100 * correct / answered) if answered else 0
    return {"answered": answered, "correct": correct,
            "accuracy": accuracy, "next_due": earliest}


def summary_html(summary: dict) -> str:
    """Session-end summary HTML; stable id='session' anchor."""
    s = summary if isinstance(summary, dict) else {}
    answered = int(s.get("answered", 0) or 0)
    accuracy = int(s.get("accuracy", 0) or 0)
    nxt = html.escape(str(s.get("next_due", "") or "—"))
    return (
        f"<div id='session'><p>{answered} answered · "
        f"{accuracy}% accuracy · next due {nxt}.</p></div>"
    )
