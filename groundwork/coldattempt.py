"""Productive-failure sessions (F-56): attempt cold before any study, primed.

Builds a small cold-attempt queue over *unseen* concepts only — never
owned, never due — each with a priming line ("attempt cold, then study
— struggle first"). Mirrors minisession.py's queue-spec shape (a list
of ``{"concept_id": ...}`` dicts) so cold sessions compose with the
session infra, and serendipity.py's adjacent-concept bonus (candidates
sharing a module with something already owned sort first). Pure
functions, stdlib only, no groundwork imports, no DB/schema. Every
public helper fails closed and never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b12-coldattempt"

DEFAULT_SIZE = 3
MAX_SIZE = 12

PRIME_PHRASE = "attempt cold, then study — struggle first"


def _cid_of(concept) -> str:
    """Concept id from ``id`` (preferred) or ``concept_id``; "" when absent."""
    try:
        if not isinstance(concept, dict):
            return ""
        for key in ("id", "concept_id"):
            val = concept.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
            if val is not None and not isinstance(val, str):
                text = str(val).strip()
                if text:
                    return text
        return ""
    except Exception:  # noqa: BLE001 -- id lookup must never raise
        return ""


def _mid_of(concept) -> str:
    """Module id from ``module_id`` (preferred) or ``mid``; "" when absent."""
    try:
        if not isinstance(concept, dict):
            return ""
        for key in ("module_id", "mid"):
            val = concept.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
            if val is not None and not isinstance(val, str):
                text = str(val).strip()
                if text:
                    return text
        return ""
    except Exception:  # noqa: BLE001 -- module lookup must never raise
        return ""


def _as_set(ids) -> set:
    """Normalize owned/due ids to a str set; hostile input becomes empty."""
    try:
        if ids is None:
            return set()
        if isinstance(ids, (str, bytes)):
            return {ids} if ids else set()
        return {str(i).strip() for i in ids
                if str(i).strip() and not isinstance(i, dict)}
    except Exception:  # noqa: BLE001 -- set coercion must never raise
        try:
            return {str(ids)}
        except Exception:  # noqa: BLE001 -- last resort
            return set()


def _size_of(size) -> int:
    """Clamp queue size to 0..MAX_SIZE; hostile input fails closed."""
    try:
        n = int(size)
        if n < 0:
            return 0
        return min(n, MAX_SIZE)
    except Exception:  # noqa: BLE001 -- size lookup must never raise
        return DEFAULT_SIZE


def _label(concept, cid: str) -> str:
    """Human label for the prime line; falls back to the concept id."""
    try:
        for key in ("name", "concept", "title"):
            val = concept.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        return cid
    except Exception:  # noqa: BLE001 -- label lookup must never raise
        return cid


def prime_for(concept, cid: str = "") -> str:
    """Priming line for one cold concept; never raises."""
    try:
        cid = cid or _cid_of(concept)
        label = _label(concept, cid or "it")
        return f"{PRIME_PHRASE} ({label})"
    except Exception:  # noqa: BLE001 -- prime must never raise
        return PRIME_PHRASE


def cold_session(concepts, owned_ids=None, due_ids=None,
                 size=DEFAULT_SIZE) -> dict:
    """Pick up to ``size`` unseen, non-due concepts, adjacent-first.

    Unseen means not in ``owned_ids`` and not in ``due_ids`` (both
    compared as strings). Adjacent means sharing a module with an
    owned concept (serendipity-style bonus); adjacency only reorders,
    never admits owned/due ids. Empty pool fails closed to
    ``{"items": [], "note": ...}``. Never raises; never mutates inputs.
    """
    try:
        owned = _as_set(owned_ids)
        due = _as_set(due_ids)
        want = _size_of(size)
        rows = [c for c in (concepts or []) if isinstance(c, dict)]
        owned_mids = {_mid_of(c) for c in rows
                      if _cid_of(c) in owned and _mid_of(c)}
        pool = []
        seen = set()
        for concept in rows:
            cid = _cid_of(concept)
            if not cid or cid in owned or cid in due:
                continue
            if cid in seen:
                continue
            seen.add(cid)
            mid = _mid_of(concept)
            adjacent = 0 if (mid and mid in owned_mids) else 1
            pool.append((adjacent, cid, concept))
        pool.sort(key=lambda t: (t[0], t[1]))
        items = [{"concept_id": cid,
                  "prime": prime_for(concept, cid)}
                 for _, cid, concept in pool[:want]]
        if not items:
            return {"items": [],
                    "note": ("No unseen concepts left — everything "
                             "is owned or already due.")}
        noun = "concept" if len(items) == 1 else "concepts"
        return {"items": items,
                "note": (f"{len(items)} cold {noun} — attempt each "
                         "before studying.")}
    except Exception:  # noqa: BLE001 -- cold picker must never raise
        return {"items": [],
                "note": "Cold picks unavailable — showing nothing."}


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        anchor = STATUS_ANCHOR
    except Exception:  # noqa: BLE001 -- status must never raise
        anchor = "status-b12-coldattempt"
    return (
        f"<h3 id='{anchor}'>Cold-attempt sessions "
        "<small>(feature)</small></h3>"
        "<p>Attempt unseen concepts cold before any study — struggle "
        "first, then learn. <code>groundwork/coldattempt.py</code> provides "
        "<code>cold_session()</code> (unseen non-due picks, adjacent-module "
        "first, priming line each, empty pool fails closed to no items) in "
        "the minisession queue-spec shape so cold sessions compose with the "
        "session infra.</p>"
    )


def tour_entry() -> dict:
    """Tour registry entry for the cold-attempt feature; never raises."""
    try:
        return {"id": "cold-attempt", "kind": "feature",
                "title": "Cold-attempt sessions",
                "blurb": ("Attempt unseen concepts cold before studying "
                          "— struggle first, then learn."),
                "path": "/status", "anchor": STATUS_ANCHOR}
    except Exception:  # noqa: BLE001 -- tour entry must never raise
        return {"id": "cold-attempt", "kind": "feature",
                "title": "Cold-attempt sessions",
                "blurb": "Attempt cold before studying.",
                "path": "/status", "anchor": "status-b12-coldattempt"}
