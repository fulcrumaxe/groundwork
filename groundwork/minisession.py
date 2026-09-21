"""One-click 5-minute session (I-46).

Builds a ~5-minute queue from the due list using per-card time
estimates, plus the Due-page banner that starts it. Pure functions,
stdlib only, no I/O.

Planning rule: most-overdue first (``due`` ascending, ``id``
tiebreak), greedily keeping each card while the running total stays
inside ``minutes * 60`` seconds. Returns a new list; the input is
never mutated. When anything is due, at least the single
most-overdue card is returned so the button always starts something.

Cost model: a never-attempted card costs NEW_SECS (default 30); a
reviewed card costs REVIEW_SECS (default 20). A card counts as new
when it carries an explicit ``attempts``/``tries``/``reviews`` count
of 0 — or when no attempt signal is present, so the budget errs
toward promising less than 5 minutes rather than more. Pass
``estimate_fn`` (``card -> seconds``) to override per card, e.g.
closing over ``queries.attempts``; ``new_secs``/``review_secs``
retune the default model.

Boundary: planning + banner snippet live here. Grading and queue
rendering stay with cards.py/queue.py; the session-end summary
stays with session.py.
"""
from __future__ import annotations

import html

DEFAULT_MINUTES = 5
NEW_SECS = 30
REVIEW_SECS = 20

_MISSING_DUE = "\uffff"


def _is_new(card: dict) -> bool:
    """True when the card looks never-attempted (cost model)."""
    for key in ("attempts", "tries", "reviews"):
        if key in card:
            try:
                return int(card[key]) <= 0
            except (TypeError, ValueError):
                return True
    return True


def estimate_for(card, estimate_fn=None, new_secs=NEW_SECS,
                 review_secs=REVIEW_SECS) -> float:
    """Seconds one card should cost; hostile input gets the default."""
    if callable(estimate_fn):
        try:
            return max(0.0, float(estimate_fn(card)))
        except (TypeError, ValueError):
            pass
    try:
        new = int(new_secs)
    except (TypeError, ValueError):
        new = NEW_SECS
    try:
        review = int(review_secs)
    except (TypeError, ValueError):
        review = REVIEW_SECS
    if not isinstance(card, dict) or _is_new(card):
        return float(max(0, new))
    return float(max(0, review))


def _due_key(card: dict):
    """Most-overdue first; missing due sorts last; id breaks ties."""
    due = card.get("due") if isinstance(card, dict) else ""
    due = due if isinstance(due, str) and due else _MISSING_DUE
    cid = card.get("id", "") if isinstance(card, dict) else ""
    return (due, str(cid))


def pick_cards(due, minutes=DEFAULT_MINUTES, estimate_fn=None,
               new_secs=NEW_SECS, review_secs=REVIEW_SECS) -> list:
    """Most-overdue prefix of ``due`` fitting in ``minutes`` of estimates.

    Non-dict entries are skipped; bad ``minutes`` falls back to
    DEFAULT_MINUTES; a non-empty queue always yields >= 1 card.
    """
    rows = [c for c in (due or []) if isinstance(c, dict)]
    try:
        budget = float(minutes) * 60.0
    except (TypeError, ValueError):
        budget = float(DEFAULT_MINUTES) * 60.0
    budget = max(0.0, budget)
    ordered = sorted(rows, key=_due_key)
    picks: list = []
    total = 0.0
    for card in ordered:
        est = estimate_for(card, estimate_fn, new_secs, review_secs)
        if total + est > budget:
            break
        picks.append(card)
        total += est
    if not picks and ordered:
        picks.append(ordered[0])
    return picks


def planned_seconds(picks, estimate_fn=None, new_secs=NEW_SECS,
                    review_secs=REVIEW_SECS) -> float:
    """Summed estimate for an already-picked list."""
    total = 0.0
    for card in picks or []:
        total += estimate_for(card, estimate_fn, new_secs, review_secs)
    return total


def session_box_html(due, minutes=DEFAULT_MINUTES, estimate_fn=None,
                     new_secs=NEW_SECS, review_secs=REVIEW_SECS) -> str:
    """Due-page banner: start button plus 'about N cards, ~M min' copy.

    Always renders (calm all-clear, no button, when nothing is due)
    so the ``minisession`` anchor never moves. The start link targets
    the lead-card ``#up-next`` tag, which is the picked set's first
    card since picks are most-overdue-first.
    """
    picks = pick_cards(due, minutes, estimate_fn, new_secs, review_secs)
    if not picks:
        return ("<section id='minisession'><p>All clear — nothing due. "
                "Browse a module to learn ahead.</p></section>")
    secs = planned_seconds(picks, estimate_fn, new_secs, review_secs)
    mins = max(1, round(secs / 60.0))
    n = len(picks)
    try:
        label = int(minutes)
    except (TypeError, ValueError):
        label = DEFAULT_MINUTES
    noun = "card" if n == 1 else "cards"
    return (
        f"<section id='minisession'><p>About {n} {noun}, "
        f"~{mins} min. <a id='mini-start' href='#up-next'>"
        f"Start {html.escape(str(label))}-minute session</a>.</p></section>"
    )


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b9-minisession'>Five-minute session "
        "<small>(improvement)</small></h3>"
        "<p>One click queues about five minutes of the most-overdue "
        "cards — new cards budgeted at 30s, reviews at 20s — and starts "
        "you on them. <code>groundwork/minisession.py</code> provides "
        "<code>pick_cards()</code> (greedy most-overdue fill against a "
        "seconds budget, never mutates its input) and "
        "<code>session_box_html()</code> (Due banner with the start "
        "button and 'about N cards' copy).</p>"
    )
