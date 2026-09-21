"""Retrieval-first modules (F-63): questions before prose, enforced.

Lessons explain first and quiz later, so learners skim the prose and
meet the question already knowing the answer — fluency without
recall. Retrieval-first flips the order: attempt, then read. This
module owns the template: blocks are ``(kind, text)`` with kind in
``{"question", "prose"}``; ``check_order`` passes only when no prose
precedes the first question; ``enforce_template`` stably moves
questions first (unknown kinds keep their relative place at the end);
``lesson_html`` renders the enforced order with the question styled
as the retrieval prompt. Db-free library — generation templates are
untouched; pure functions, stdlib only (``html``), no I/O, no DB.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b13-retrieval"

QUESTION = "question"
PROSE = "prose"


def clean_blocks(blocks) -> list[tuple[str, str]]:
    """Usable blocks: known kinds, non-blank text, order kept."""
    out = []
    try:
        for b in blocks or []:
            try:
                kind, text = b
            except Exception:  # noqa: BLE001 -- bad block, skip it
                continue
            kind = str(kind).strip().lower() if kind is not None else ""
            text = str(text).strip() if text is not None else ""
            if kind not in (QUESTION, PROSE) or not text:
                continue
            out.append((kind, text))
        return out
    except Exception:  # noqa: BLE001 -- template must never raise
        return []


def check_order(blocks) -> bool:
    """True when the lesson retrieves before it explains.

    Vacuously true with no question (nothing to retrieve) and with
    no blocks at all; false the moment any prose precedes the first
    question.
    """
    try:
        items = clean_blocks(blocks)
        seen_prose = False
        for kind, _ in items:
            if kind == PROSE:
                seen_prose = True
            elif kind == QUESTION:
                return not seen_prose
        return True
    except Exception:  # noqa: BLE001 -- check must never raise
        return False


def enforce_template(blocks) -> list[tuple[str, str]]:
    """Stable reorder: questions first, then prose. Never raises."""
    try:
        items = clean_blocks(blocks)
        return ([b for b in items if b[0] == QUESTION]
                + [b for b in items if b[0] == PROSE])
    except Exception:  # noqa: BLE001 -- template must never raise
        return []


def lesson_html(blocks) -> str:
    """Render the enforced order: retrieval prompt, then explanation."""
    try:
        parts = ["<article class='retrieval-first'>"]
        for kind, text in enforce_template(blocks):
            safe = html.escape(text)
            if kind == QUESTION:
                parts.append(
                    f"<p class='retrieve-q'><b>Recall first:</b> {safe}</p>")
            else:
                parts.append(f"<p>{safe}</p>")
        parts.append("</article>")
        return "".join(parts)
    except Exception:  # noqa: BLE001 -- render must never raise
        return "<article class='retrieval-first'></article>"


def section_html() -> str:
    """Status-page subsection with a live enforced lesson."""
    demo = lesson_html([
        (PROSE, "Backoff doubles the sleep after each failure."),
        (QUESTION, "A call fails three times with base 1s — how long is the third sleep?"),
    ])
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Retrieval-first lessons <small>(feature)</small></h3>"
        "<p>Lessons now ask before they tell: "
        "<code>groundwork/retrieval.py</code> provides "
        "<code>check_order()</code> (no prose before the first "
        "question), <code>enforce_template()</code> (stable "
        "questions-first reorder), and <code>lesson_html()</code>, a "
        "db-free library the generation templates do not touch. The "
        "sample below arrived prose-first and renders question-first."
        "</p>" + demo)


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "retrieval-first",
        "kind": "feature",
        "title": "Retrieval-first lessons",
        "blurb": "Every lesson asks before it tells — attempt first, then read the explanation.",
        "path": "/status",
        "anchor": "status-b13-retrieval",
    }
