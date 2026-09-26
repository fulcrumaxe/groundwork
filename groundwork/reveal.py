"""Give-up reveal: surrender logs grade 0, answer shows after (I-158).

The Due queue already hides the answer until after the attempt
(web.py renders ``back`` only on the graded result page) and already
renders a give-up form (cards.answer_widget posts a blank answer with
floor confidence to the same review endpoint). What is missing: the
give-up currently grades like a near-miss — recall cards parse the
blank as rating 0, but every other type maps fail to grade 1
(mcp.MCPServer.submit_review). This module owns the surrender shape
and the grade-0 result so the one caller can branch before per-type
grading. Pure functions, stdlib only (``html``), no I/O, no DB or
schema changes, no web.py edits. Lapse bookkeeping stays in sched
(I-159 owns that item, not this one).
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b24-reveal"

GIVEUP_CONFIDENCE = 1

REVEAL_FEEDBACK = ("Gave up — the answer is revealed below. "
                   "Logged as grade 0.")


def is_reveal_request(submission="", confidence: int = 3) -> bool:
    """True only for the give-up post: blank answer + floor confidence.

    Anything else — real text, a real 0-5 rating with normal
    confidence, unparseable types — is a genuine attempt and grades
    normally. Never raises; non-string submissions are attempts.
    """
    try:
        if not isinstance(submission, str):
            return False
        if submission.strip():
            return False
        return int(confidence) == GIVEUP_CONFIDENCE
    except (TypeError, ValueError):
        return False


def reveal_result(card=None) -> dict:
    """Grade-0 result for a surrender; back text stays caller-owned.

    Returns ``pass=False, score=0.0`` plus feedback. When a card dict
    with a ``back`` string is supplied the feedback names the reveal;
    otherwise (legacy/missing data) it stays generic — still grade 0.
    Never raises.
    """
    try:
        back = ""
        if isinstance(card, dict):
            raw = card.get("back", "")
            back = raw if isinstance(raw, str) else ""
        if back.strip():
            feedback = (REVEAL_FEEDBACK + f" Answer: {back.strip()}")
        else:
            feedback = REVEAL_FEEDBACK
    except Exception:  # noqa: BLE001 -- grading must never raise
        feedback = REVEAL_FEEDBACK
    return {"pass": False, "score": 0.0, "feedback": feedback,
            "grade": 0, "revealed": True}


def back_visible(has_attempted: bool = False) -> bool:
    """The answer may render only after an attempt is recorded.

    Encodes the already-enforced principle so future renderers share
    one predicate: no attempt, no back. Truthy/falsy coerced; never
    raises.
    """
    try:
        return bool(has_attempted)
    except Exception:  # noqa: BLE001 -- predicate must never raise
        return False


def section_html() -> str:
    """Status-page subsection with a live surrender example."""
    try:
        demo = reveal_result({"back": "Paris"})["feedback"]
    except Exception:  # noqa: BLE001 -- status must never raise
        demo = REVEAL_FEEDBACK
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Give-up reveal <small>(improvement)</small></h3>"
        "<p>Giving up now logs an honest grade 0 on every card type "
        "(before: non-recall surrenders scored 1, like a near-miss) and "
        "the answer appears only after the attempt is recorded: "
        "<code>groundwork/reveal.py</code> provides "
        "<code>is_reveal_request()</code> plus "
        "<code>reveal_result()</code>, called from "
        "<code>MCPServer.submit_review</code> with no route, schema, or "
        "web.py changes. Lapse counting stays in sched (separate item).</p>"
        f"<p><small>{html.escape(demo)}</small></p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "reveal-grade-zero",
        "kind": "improvement",
        "title": "Give-up reveal logs 0",
        "blurb": "Stuck? Give up reveals the answer after logging an honest grade 0 on any card.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
