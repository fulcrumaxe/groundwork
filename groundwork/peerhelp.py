"""Peer level hints (I-124): tabs note which level helped peers most.

Votes are opt-in (level, opted) pairs; the winner needs a strict
plurality with a quorum of three. With no winner the line renders as
the empty string, so the lesson path stays byte-identical until
quorum. Stdlib only (``html``); no I/O, never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b20-peerhelp"

LEVELS = (1, 2, 3, 4)
QUORUM = 3


def _level_name(level) -> str:
    try:
        from . import explain as explainmod
        return explainmod.LEVEL_TITLES.get(int(level), f"Level {int(level)}")
    except Exception:  # noqa: BLE001
        return f"Level {level}"


def normalize_vote(vote):
    """(level, True) for an opt-in vote with a valid level; None else."""
    try:
        if isinstance(vote, dict):
            level, opted = vote.get("level"), vote.get("opted")
        else:
            level, opted = vote[0], vote[1]
        if opted is not True:
            return None
        level = int(level)
        if level not in LEVELS:
            return None
        return (level, True)
    except (TypeError, ValueError, IndexError, KeyError):
        return None


def aggregate(votes) -> dict | None:
    """{"winner", "votes", "total"} on strict plurality + quorum; else None.

    Ties and sub-quorum counts return None (legacy silence). Never raises.
    """
    try:
        counts = {level: 0 for level in LEVELS}
        total = 0
        for vote in votes or []:
            norm = normalize_vote(vote)
            if norm is None:
                continue
            counts[norm[0]] += 1
            total += 1
        if total < QUORUM:
            return None
        ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        if ranked[0][1] == ranked[1][1]:
            return None
        return {"winner": ranked[0][0], "votes": ranked[0][1], "total": total}
    except Exception:  # noqa: BLE001
        return None


def line_html(votes) -> str:
    """One-line peer verdict; "" with no winner (legacy bytes)."""
    try:
        agg = aggregate(votes)
        if not agg:
            return ""
        name = _level_name(agg["winner"])
        return (
            f"<p class='peerhelp'>Peers found {html.escape(name)} most "
            f"helpful ({agg['votes']} of {agg['total']} opt-in votes).</p>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    sample = line_html([(3, True)] * 4 + [(2, True)])
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Peer level hint <small>(improvement)</small></h3>"
        "<p>Tabs note which level opted-in peers found most helpful — "
        "silent until quorum. <code>groundwork/peerhelp.py</code> counts "
        "only opt-in votes on the lesson rendering path "
        "(<code>lessons.render_levels</code>); ties and thin counts "
        "render nothing. A live sample renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "peer-level-hint",
        "kind": "improvement",
        "title": "Peer level hint",
        "blurb": "Tabs note which level opted-in peers found most "
                 "helpful; silent until quorum.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
