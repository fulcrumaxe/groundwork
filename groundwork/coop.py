"""Co-op card splits (F-127): complementary hands for two learners.

One machine, two learners, one due queue. ``deal`` walks the already
ordered due list and hands cards out alternately (A, B, A, B ...) so
the hands are disjoint and together cover every card — neither learner
repeats the other, and no card is left out. Names and pane labelling
are owned by ``buddyview`` (delegated, never duplicated); ordering is
owned by ``sched``/``forgetcurve`` (coop never re-sorts). Pure
functions, stdlib ``html`` only at top level, no I/O, no DB changes,
never raises: anything unusable falls back to empty hands / ``""`` so
the Due page renders byte-identical to the solo queue. The caller is
``Handler.due_html`` (?buddy= pair atop the queue).
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b24-coop"


def _clean_name(value) -> str:
    """Display name or ""; buddyview owns this rule, fallback is local."""
    try:
        from . import buddyview as _buddy
        return _buddy.clean_name(value)
    except Exception:  # noqa: BLE001 -- names must never raise
        try:
            if not isinstance(value, str):
                return ""
            return value.strip()[:40]
        except Exception:  # noqa: BLE001
            return ""


def duo(friends) -> list:
    """Two distinct cleaned names, or [] (solo/hostile stays solo)."""
    try:
        names = []
        for f in (friends or []):
            n = _clean_name(f)
            if n and n not in names:
                names.append(n)
        return names[:2] if len(names) >= 2 else []
    except Exception:  # noqa: BLE001 -- duo must never raise
        return []


def _cards(due) -> list:
    """Dict cards only, in queue order; garbage rows are dropped."""
    try:
        items = list(due or [])
    except TypeError:
        return []
    return [c for c in items if isinstance(c, dict)]


def deal(due, friends=None) -> tuple:
    """(hand_a, hand_b) dealt alternately off the live due order.

    Complementary: disjoint, covering every card, each hand keeping
    queue order. Fewer than two cards, fewer than two distinct names,
    or hostile input gives ([], []) — the solo fallback. Never raises.
    """
    try:
        cards = _cards(due)
        if len(cards) < 2 or (friends is not None and not duo(friends)):
            return [], []
        hand_a, hand_b = [], []
        for i, c in enumerate(cards):
            (hand_a if i % 2 == 0 else hand_b).append(c)
        return hand_a, hand_b
    except Exception:  # noqa: BLE001 -- dealing must never raise
        return [], []


def is_complementary(hand_a, hand_b, due) -> bool:
    """True when both hands together cover the due list exactly once."""
    try:
        want = _cards(due)
        got_a = list(hand_a or [])
        got_b = list(hand_b or [])
        if len(got_a) + len(got_b) != len(want):
            return False
        # Degenerate audits fail closed: a real split always covers 2+.
        if len(want) < 2:
            return False
        seen = {id(c) for c in got_a}
        if len(seen) != len(got_a):
            return False
        for c in got_b:
            if id(c) in seen:
                return False
            seen.add(id(c))
        return seen == {id(c) for c in want}
    except Exception:  # noqa: BLE001 -- audit must never raise
        return False


def _title(card: dict) -> str:
    """Escaped one-line label for a dealt card."""
    try:
        concept = html.escape(str(card.get("concept_id") or "unfiled"))
        cid = html.escape(str(card.get("id") or "?"))
        return f"{concept} <small>{cid}</small>"
    except Exception:  # noqa: BLE001 -- labels must never raise
        return "card"


def _pane(who: str, hand) -> str:
    """One labelled hand; pane chrome delegated to buddyview."""
    try:
        from . import buddyview as _buddy
        pane = _buddy.pane_html("Co-op hand", who)
    except Exception:  # noqa: BLE001
        pane = (f"<div class='buddy-pane'><h4>Co-op hand "
                f"<small>({html.escape(who)})</small></h4></div>")
    try:
        rows = "".join(f"<li>{_title(c)}</li>" for c in (hand or []))
        return f"{pane}<ol class='coop-hand'>{rows}</ol>"
    except Exception:  # noqa: BLE001 -- panes must never raise
        return ""


def split_html(due, friends) -> str:
    """Co-op split section; "" unless a valid duo split exists."""
    try:
        names = duo(friends)
        cards = _cards(due)
        if len(names) < 2 or len(cards) < 2:
            return ""
        hand_a, hand_b = deal(cards)
        if not hand_a or not hand_b:
            return ""
        return (
            "<div class='coop-split'>"
            f"<h3>Co-op split — {html.escape(names[0])} vs "
            f"{html.escape(names[1])}</h3>"
            f"<p><small>{len(hand_a)} + {len(hand_b)} cards, "
            "no repeats, none left out.</small></p>"
            f"{_pane(names[0], hand_a)}{_pane(names[1], hand_b)}</div>")
    except Exception:  # noqa: BLE001 -- view must never raise
        return ""


def entry_hint() -> str:
    """Hint wired next to the buddy entry form; always safe to render."""
    try:
        return ("<p class='coop-hint'><small>Two names split the due "
                "queue into complementary hands — same form, no extra "
                "setup.</small></p>")
    except Exception:  # noqa: BLE001
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch24.py."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Co-op card splits "
            "<small>(feature)</small></h3>"
            "<p>Two learners, one queue, no doubled work: "
            "<code>groundwork/coop.py</code> deals the live Due queue "
            "alternately into two complementary hands (disjoint, covering "
            "every card), labelled with <code>buddyview</code> panes, "
            "local only — solo visits render exactly as before.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Co-op card splits</h3>"
                "<p>Co-op help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "coop-splits",
        "kind": "feature",
        "title": "Co-op card splits",
        "blurb": ("Two learners split the due queue — complementary hands, no repeats, local only."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
