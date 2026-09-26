"""Honest Give-up path: a blank submit records a lapse, schedules sooner (I-159).

The Due queue's Give-up button POSTs an empty answer to the normal review
route (``cards.answer_widget``). The surrender branch in
``MCPServer.submit_review`` (I-158) logs grade 0; this module adds the
second half of honesty: the lapse count increments (``cards.lapses`` —
a real schema column shown in the due-why tooltip — stayed 0 forever
because no UPDATE ever wrote it) and the result names the cost, while
scheduling flows through ``sched.review_card`` with the honest grade
so stability halves and the card returns in about a day.

Boundary — this module owns ONLY blank detection + lapse application:
``is_giveup`` / ``apply_giveup`` / ``next_lapses`` / ``lapse_line``
plus the status/tour hooks below. Reveal rendering stays with I-158,
grading with ``exercises.grade``, persistence with
``MCPServer.submit_review`` (which adds ``lapses`` to its existing
card UPDATE — no schema change, the column already exists). Pure
functions, stdlib only, never raises.
"""
from __future__ import annotations

from datetime import datetime

STATUS_ANCHOR = "status-b24-giveup"

#: The honest grade for every give-up, all exercise types alike.
GIVEUP_GRADE = 0


def is_giveup(submission) -> bool:
    """True when the submission is a give-up: missing, empty, or blank.

    Anything with a non-whitespace character is a real attempt and grades
    exactly as today (legacy fallback). Never raises.
    """
    try:
        if submission is None:
            return True
        return not str(submission).strip()
    except Exception:  # noqa: BLE001 -- detection never blocks grading
        return False


def _num(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _lapses(value) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def next_lapses(lapses) -> int:
    """Lapse count after one more surrender; fail-closed, never raises."""
    try:
        return _lapses(lapses) + 1
    except Exception:  # noqa: BLE001
        return 1


def apply_giveup(stability, difficulty, lapses,
                 now: datetime | None = None, grades=None) -> dict:
    """Honest FSRS review for a give-up: grade-0 collapse plus one lapse.

    Delegates scheduling to ``sched.review_card`` with ``GIVEUP_GRADE``
    so the due date comes from the same model as every other fail;
    ``grades`` (oldest-first history including this 0) rides through
    untouched. Returns the scheduler dict plus ``lapses`` and ``grade``.
    Bad card numbers coerce fail-closed; never raises.
    """
    from . import sched as schedmod
    try:
        upd = schedmod.review_card(_num(stability, 1.0),
                                   _num(difficulty, 0.5),
                                   GIVEUP_GRADE, now=now, grades=grades)
    except Exception:  # noqa: BLE001 -- caller still banks the lapse
        upd = {"stability": 0.5, "difficulty": 0.6,
               "retrievability": 1.0,
               "due": schedmod.iso(schedmod.utcnow())}
    upd["lapses"] = _lapses(lapses) + 1
    upd["grade"] = GIVEUP_GRADE
    return upd


def lapse_line(lapses) -> str:
    """One honest line for the result screen: what giving up cost."""
    n = _lapses(lapses)
    word = "lapse" if n == 1 else "lapses"
    return (f"Recorded as a lapse ({n} {word} on this card) — "
            "it returns sooner until it sticks.")


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch24.py."""
    try:
        sample = lapse_line(1)
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Honest give-up <small>(improvement)</small></h3>"
            "<p>Giving up stops pretending: <code>groundwork/giveup.py</code> "
            "detects the blank submit on the learner path "
            "(<code>cards.answer_widget</code> → "
            "<code>POST /cards/{cid}/review</code> → "
            "<code>MCPServer.submit_review</code>), scores it an honest "
            "grade 0 through <code>sched.review_card</code> so stability "
            "halves and the card returns in about a day, and increments "
            "the long-dead <code>cards.lapses</code> counter the due-why "
            "tooltip already displays. Reveal rendering stays with I-158. "
            f"Sample: {sample}</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Honest give-up</h3>"
                "<p>Give-up help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "giveup-lapse",
        "kind": "improvement",
        "title": "Honest give-up",
        "blurb": ("Giving up records a lapse and brings the card back "
                  "sooner — the scheduler tells the truth."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
