"""Concepts-owned counter as the headline number (F-102).

Streaks never appear: the History page opens with how many concepts
the learner can prove they own (a spaced modify/create pass plus a
return visit, per ownership.py), out of how many exist. Pure
computation over the existing reviews/cards/concepts tables — no
schema change, no new storage.

Caller path (History page, never a Status demo):
``history.history_html`` prepends ``headline_html`` so the first
thing a returning learner sees is owned proof, not attempt volume.
The block always renders (anchor-stable for the tour); with no
concepts it says 0 with a next action. Never raises.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import ownership as ownmod

STATUS_ANCHOR = "status-b22-ownhead"


def counts(db_path: str) -> dict:
    """{"owned": int, "concepts": int} over the whole library.

    Same owned rule as ownership.owned_map (passing modify/create
    review plus 2+ attempts), applied per concept in one query.
    Hostile input or a missing DB yields zeros; never raises.
    """
    try:
        types = ownmod.ownership_types()
        con = dbmod.connect(db_path)
        try:
            if types:
                placeholders = ",".join("?" * len(types))
                own_case = (
                    "SUM(CASE WHEN reviews.grade >= 4"
                    f" AND cards.exercise_type IN ({placeholders})"
                    " THEN 1 ELSE 0 END) AS own_pass")
                args: list = list(types)
            else:
                own_case = "0 AS own_pass"
                args = []
            rows = con.execute(
                "SELECT concepts.id AS cid, COUNT(reviews.id) AS attempts,"
                f" {own_case} FROM concepts"
                " LEFT JOIN cards ON cards.concept_id = concepts.id"
                " LEFT JOIN reviews ON reviews.card_id = cards.id"
                " GROUP BY concepts.id", args).fetchall()
        finally:
            con.close()
        owned = sum(1 for r in rows
                    if (r["own_pass"] or 0) and (r["attempts"] or 0) >= 2)
        return {"owned": owned, "concepts": len(rows)}
    except Exception:  # noqa: BLE001 -- headline never breaks history
        return {"owned": 0, "concepts": 0}


def headline_html(db_path: str) -> str:
    """Always-rendered owned-proof headline for history.history_html.

    The anchor never moves (the tour points at it); empty libraries
    get a 0-count with a next action instead of nothing. Escapes
    nothing (counts are ints); never raises.
    """
    try:
        c = counts(db_path)
        owned, total = int(c["owned"]), int(c["concepts"])
    except Exception:  # noqa: BLE001 -- headline never breaks history
        owned, total = 0, 0
    try:
        if total <= 0:
            return ("<p id='owned-headline'><b>0 concepts owned</b> — "
                    "answer a card on the <a href='/due'>Due</a> page "
                    "and proof starts here. Streaks are never counted, "
                    "only owned concepts.</p>")
        return (f"<p id='owned-headline'><b>{owned} concept"
                f"{'' if owned == 1 else 's'} owned</b> of {total} — "
                "streaks are never counted, only proof.</p>")
    except Exception:  # noqa: BLE001 -- headline never breaks history
        return ("<p id='owned-headline'><b>0 concepts owned</b>.</p>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        sample = headline_html(":memory:")
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Owned headline "
            "<small>(feature)</small></h3>"
            "<p>History opens with concepts owned, never streaks — "
            "<code>groundwork/ownhead.py</code> counts spaced "
            "modify/create passes over the existing tables and "
            "<code>history.history_html</code> prepends the headline; "
            "empty libraries get a 0-count with a next action.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Owned headline</h3>"
                "<p>Owned-headline help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "owned-headline",
        "kind": "feature",
        "title": "Concepts owned, up top",
        "blurb": ("History opens with the concepts you can prove — "
                  "streaks are never counted."),
        "path": "/reviews",
        "anchor": "owned-headline",
    }
