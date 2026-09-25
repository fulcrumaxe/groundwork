"""Difficulty-vote exercise weights for the Due queue (I-146).

Votes captured by diffvote.py (I-145) reshape practice: a concept
voted too-easy leads with its hardest-tier card, a concept voted
too-hard consolidates from its lowest tier first, and unvoted
concepts keep today's order byte-identical. weights_for() names
the per-tier emphasis (easy favors create, hard favors recall);
order_due() applies it as a stable within-concept reorder, so
upstream bridges (interleave, kata, boredom, remediation) survive.
Empty or hostile votes keep the queue untouched; never raises.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b23-diffweights"

_EASY = {"recall": 0.5, "explain": 0.75, "apply": 1.0,
         "analyse": 1.5, "modify": 2.0, "create": 2.0}
_HARD = {"recall": 2.0, "explain": 1.5, "apply": 1.0,
         "analyse": 0.75, "modify": 0.5, "create": 0.5}


def weights_for(vote) -> dict:
    """Per-tier emphasis for one vote; just/unknown reads uniform."""
    try:
        from . import debt as debtmod
        rungs = list(debtmod.BLOOM_RUNGS)
    except Exception:  # noqa: BLE001 -- weights must never raise
        return {}
    try:
        from . import diffvote as diffvotemod
        norm = (diffvotemod.normalize_vote(vote) if not isinstance(vote, dict)
                else _plurality(vote))
    except Exception:  # noqa: BLE001 -- votes must never raise
        norm = ""
    table = _EASY if norm == "easy" else _HARD if norm == "hard" else None
    if table is None:
        return {r: 1.0 for r in rungs}
    return {r: float(table.get(r, 1.0)) for r in rungs}


def _plurality(tally) -> str:
    """Plurality vote of a tally dict; ties read just (uniform)."""
    try:
        counts = {v: int(tally.get(v, 0) or 0)
                  for v in ("easy", "just", "hard")}
    except (TypeError, ValueError, AttributeError):
        return ""
    if sum(counts.values()) == 0:
        return ""
    top = max(counts.values())
    winners = [v for v in ("easy", "just", "hard") if counts[v] == top]
    return winners[0] if len(winners) == 1 else "just"


def _vote_of(votes, cid) -> str:
    """Normalized vote for one concept id; "" keeps legacy order."""
    try:
        if not isinstance(votes, dict):
            return ""
        raw = votes.get(cid)
        if isinstance(raw, dict):
            return _plurality(raw)
        from . import diffvote as diffvotemod
        return diffvotemod.normalize_vote(raw)
    except Exception:  # noqa: BLE001 -- lookup must never raise
        return ""


def order_due(cards, votes=None) -> list:
    """Due queue with voted concepts reweighted; pure stable reorder.

    Within each voted concept, cards sort by their vote's tier
    weight (hard recalls first, easy creates first); concepts keep
    their input order and unvoted concepts keep their card order,
    so no votes means byte-identical output. Never drops,
    duplicates, or raises.
    """
    try:
        from . import boredom as boredommod
        if not isinstance(cards, list) or not cards:
            return list(cards) if isinstance(cards, list) else []
        groups: dict = {}
        order: list = []
        for c in cards:
            try:
                key = c.get("concept_id") if isinstance(c, dict) else None
            except AttributeError:
                key = None
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(c)
        out = []
        for key in order:
            group = groups[key]
            vote = _vote_of(votes, key)
            if vote not in ("easy", "hard"):
                out.extend(group)
                continue
            weights = weights_for(vote)
            scored = []
            for i, c in enumerate(group):
                tier = boredommod.tier_of(c)
                scored.append((0.0 - weights.get(tier, 1.0), i, c))
            scored.sort(key=lambda t: (t[0], t[1]))
            out.extend(c for _, _, c in scored)
        return out
    except Exception:  # noqa: BLE001 -- queue must never break
        return list(cards) if isinstance(cards, list) else []


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Difficulty-vote weights "
            "<small>(improvement)</small></h3>"
            "<p>Votes steer practice — "
            "<code>groundwork/diffweights.py</code> reorders the Due "
            "queue off live difficulty votes (too-easy surfaces harder "
            "types first, too-hard consolidates foundations); no votes "
            "means today's order stands.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Difficulty-vote weights</h3>"
                "<p>Vote-weight help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "difficulty-vote-weights",
        "kind": "improvement",
        "title": "Difficulty-vote exercise weights",
        "blurb": ("Too-easy votes surface harder types first; too-hard "
                  "votes consolidate foundations."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
