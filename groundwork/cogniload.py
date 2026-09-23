"""Cognitive-load guard (F-94): cap new concepts per session by strain.

A tired learner who meets five new ideas in one session keeps none of
them. This module measures strain from recent grades (pure function of
numbers the caller already has) and caps how many *distinct new*
concepts a session plan may introduce. Rested learners get the base
cap; strained learners get fewer; unknown history fails open to the
base cap so legacy callers with no data see no behavior change.

Caller path (real learner path, never a Status demo):
``minisession.pick_cards`` applies ``cap_new_concepts`` to its
budgeted picks when the caller supplies a strain signal (``recent``
grades) or newness evidence (``tried`` attempt counts); the Due page
(``Handler.due_html``) supplies both from rows it already fetches.
No signals means the legacy picks return untouched. No DB or schema
changes, no reordering — the guard only drops surplus new-concept
cards, reviews always survive, and a non-empty queue still yields at
least one card.

Legacy no-data fallback: ``recent`` empty/None/unparseable means
strain 0.0 and the base cap (3). The guard never raises and never
reorders cards — it only drops surplus new-concept cards.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b21-cogniload"

BASE_NEW_CAP = 3
MIN_NEW_CAP = 1
MAX_NEW_CAP = 5
STRAIN_WINDOW = 10
LOW_GRADE = 2


def _grade_value(g):
    """One grade 0..5 as float, or None when unparseable."""
    try:
        if isinstance(g, dict):
            for key in ("grade", "score", "rating"):
                if key in g:
                    return _grade_value(g[key])
            return None
        v = float(g)
    except (TypeError, ValueError):
        return None
    if v != v:  # NaN: unknown, never evidence of strain
        return None
    return min(5.0, max(0.0, v))


def strain_of(recent) -> float:
    """Measured strain 0..1: share of low (<=2) grades in the window.

    Uses at most the last STRAIN_WINDOW grades. Empty, None, or fully
    unparseable input means 0.0 (rested legacy fallback). Never raises.
    """
    try:
        if not recent:
            return 0.0
        vals = [_grade_value(g) for g in list(recent)[-STRAIN_WINDOW:]]
        vals = [v for v in vals if v is not None]
        if not vals:
            return 0.0
        low = sum(1 for v in vals if v <= LOW_GRADE)
        return low / len(vals)
    except Exception:  # noqa: BLE001 -- guard must never raise
        return 0.0


def new_concept_cap(recent=None, strain=None, base: int = BASE_NEW_CAP) -> int:
    """Max distinct new concepts for one session (MIN..MAX_NEW_CAP).

    Explicit ``strain`` wins; otherwise it is measured from ``recent``.
    Strain >= 0.5 -> 1, >= 0.25 -> 2, else base. ``base`` clamps into
    range; unparseable input fails closed to MIN_NEW_CAP for explicit
    bad strain, base cap for bad history. Never raises.
    """
    try:
        try:
            b = int(base)
        except (TypeError, ValueError):
            b = BASE_NEW_CAP
        b = min(MAX_NEW_CAP, max(MIN_NEW_CAP, b))
        if strain is not None:
            try:
                s = float(strain)
            except (TypeError, ValueError):
                return MIN_NEW_CAP
            if s != s:
                return b
            s = min(1.0, max(0.0, s))
        else:
            s = strain_of(recent)
        if s >= 0.5:
            return MIN_NEW_CAP
        if s >= 0.25:
            return min(b, 2)
        return b
    except Exception:  # noqa: BLE001 -- guard must never raise
        return BASE_NEW_CAP


def is_new(card: dict) -> bool:
    """True when the card introduces an unseen concept. Fail-closed False."""
    try:
        if not isinstance(card, dict):
            return False
        if card.get("is_new") is True:
            return True
        tried = card.get("attempts", card.get("reviews", card.get("n", 0)))
        try:
            if int(tried or 0) > 0:
                return False
        except (TypeError, ValueError):
            pass
        if card.get("last_review"):
            return False
        return True
    except Exception:  # noqa: BLE001 -- never raise
        return False


def _concept_of(card: dict, i: int) -> str:
    try:
        c = str(card.get("concept", "")).strip()
        return c or f"#{i}"
    except Exception:  # noqa: BLE001 -- never raise
        return f"#{i}"


def cap_new_concepts(cards, recent=None, cap=None, base: int = BASE_NEW_CAP) -> list:
    """Filter a session plan to at most ``cap`` distinct new concepts.

    Order-preserving; review cards always pass; the first ``cap``
    new concepts pass with all their cards; surplus new-concept cards
    are dropped. ``cap`` defaults to ``new_concept_cap(recent)``.
    Non-list input returns []. Never raises.
    """
    try:
        if not isinstance(cards, list):
            return []
        if cap is None:
            cap = new_concept_cap(recent, base=base)
        try:
            cap = int(cap)
        except (TypeError, ValueError):
            return list(cards)
        if cap < 0:
            cap = 0
        seen: set = set()
        out = []
        for i, card in enumerate(cards):
            try:
                if not isinstance(card, dict) or not is_new(card):
                    out.append(card)
                    continue
                key = _concept_of(card, i)
                if key in seen:
                    out.append(card)
                    continue
                if len(seen) < cap:
                    seen.add(key)
                    out.append(card)
                # else: surplus new concept, drop the card
            except Exception:  # noqa: BLE001 -- one bad card skips it
                continue
        return out
    except Exception:  # noqa: BLE001 -- guard must never raise
        try:
            return list(cards) if isinstance(cards, list) else []
        except Exception:  # noqa: BLE001
            return []


def guard_note(recent=None, cap=None) -> str:
    """One-line explanation for the session box; never raises."""
    try:
        s = strain_of(recent)
        c = cap if cap is not None else new_concept_cap(recent)
        return f"Load guard: strain {s:.0%}, at most {c} new concepts."
    except Exception:  # noqa: BLE001 -- never raise
        return "Load guard: at most 3 new concepts."


def section_html() -> str:
    """Anchored status subsection; joined by the batch21 home module."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Cognitive-load guard "
            "<small>(feature)</small></h3>"
            "<p>Strained learners meet fewer new ideas per session: "
            "<code>groundwork/cogniload.py</code> measures strain from "
            "recent grades and caps distinct new concepts on the session "
            "plan path (<code>minisession.pick_cards</code>); rested "
            "sessions keep the base cap, review cards always survive.</p>")
    except Exception:  # noqa: BLE001 -- status must never raise
        return (f"<h3 id='{STATUS_ANCHOR}'>Cognitive-load guard</h3>"
                "<p>Load-guard help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "cognitive-load-guard",
        "kind": "feature",
        "title": "Cognitive-load guard",
        "blurb": ("Strained sessions introduce fewer new concepts; "
                  "reviews always survive the cut."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
