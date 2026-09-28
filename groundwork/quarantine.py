"""Accepted-dispute quarantine: stale the card, mint a fresh retry (I-195).

When a maintainer accepts a grade dispute, the reference answer was
wrong — but the learner still owes the concept. So the disputed card
is quarantined (``stale=1`` drops it from every Due query) and a fresh
replacement takes its place with reset FSRS state, due immediately.

No pipeline run, no invented content: the pipeline never authors
teaching text, so the retry carries the same front/payload while the
maintainer fixes the back through the normal module path. Provenance
(plus the dispute reason) rides in the replacement's ``payload`` —
a data write to an existing column. No schema changes.
"""
from __future__ import annotations

import json

from . import db as dbmod
from . import sched as schedmod

SEP = "~rq"
STATUS_ANCHOR = "status-b29-quarantine"


def regen_id(card_id: str, dispute_id: int) -> str:
    """Deterministic replacement id: one regen per dispute, retry-safe."""
    return f"{card_id}{SEP}{int(dispute_id)}"


def is_regen(card_id) -> bool:
    """True when the id marks an I-195 replacement card; never raises."""
    return isinstance(card_id, str) and SEP in card_id


def replacement_for(card: dict, dispute: dict, now_iso: str) -> dict:
    """Pure builder: fresh-card row for a quarantined card + dispute.

    The question stands (only the reference was disputed), so front
    and payload carry over; scheduling resets so the retry is due
    now; payload gains provenance and the dispute reason.
    """
    card = dict(card or {})
    dispute = dict(dispute or {})
    try:
        payload = json.loads(card.get("payload") or "{}")
        if not isinstance(payload, dict):
            payload = {}
    except ValueError:
        payload = {}
    payload = dict(payload)
    payload["regen_from"] = card.get("id", "")
    payload["regen_dispute"] = dispute.get("id", "")
    reason = str(dispute.get("reason") or "").strip()[:500]
    if reason:
        payload["dispute_reason"] = reason
    return {
        "id": regen_id(str(card.get("id", "")), int(dispute.get("id") or 0)),
        "concept_id": card.get("concept_id", ""),
        "exercise_type": str(card.get("exercise_type") or "1"),
        "front": card.get("front", ""),
        "back": card.get("back", ""),
        "payload": json.dumps(payload),
        "due": now_iso,
    }


def settle_accepted(db_path: str, dispute_id: int) -> dict:
    """Quarantine + regenerate one accepted dispute; else a no-op.

    Accepted: old card ``stale=1`` (out of Due), replacement inserted
    (due now, fresh FSRS). Re-run safe: an existing regen is reused,
    never duplicated. Open/rejected/unknown disputes change nothing.
    """
    con = dbmod.connect(db_path)
    try:
        drow = con.execute(
            "SELECT * FROM disputes WHERE id=?", (dispute_id,)).fetchone()
        if drow is None:
            return {"error": "unknown dispute"}
        dispute = dict(drow)
        if dispute.get("status") != "accepted":
            return {"dispute_id": dispute_id,
                    "status": dispute.get("status"),
                    "quarantined": False}
        card_id = dispute.get("card_id", "")
        crow = con.execute(
            "SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
        if crow is None:
            return {"error": "unknown card"}
        rid = regen_id(card_id, dispute_id)
        have = con.execute(
            "SELECT id FROM cards WHERE id=?", (rid,)).fetchone()
        if have is not None:
            return {"dispute_id": dispute_id, "status": "accepted",
                    "quarantined": card_id, "regen_id": rid, "reused": True}
        new = replacement_for(
            dict(crow), dispute, schedmod.iso(schedmod.utcnow()))
        con.execute("UPDATE cards SET stale=1 WHERE id=?", (card_id,))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back,"
            " payload, due) VALUES(?,?,?,?,?,?,?)",
            (new["id"], new["concept_id"], new["exercise_type"],
             new["front"], new["back"], new["payload"], new["due"]))
        con.commit()
        return {"dispute_id": dispute_id, "status": "accepted",
                "quarantined": card_id, "regen_id": rid}
    finally:
        con.close()


def section_html() -> str:
    """Anchored status subsection; joined by the Batch 29 home module."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Dispute quarantine "
        f"<small>(improvement)</small></h3>"
        "<p>An accepted dispute retires its card from the Due queue "
        "(<code>stale=1</code>) and mints a fresh retry due immediately, "
        "with the dispute reason tucked into the new card for the "
        "maintainer. <code>groundwork/quarantine.py</code>.</p>")


def tour_entry() -> dict:
    """Tour registry entry (appended to tour.ENTRIES by the parent)."""
    return {"id": "dispute-quarantine", "kind": "improvement",
            "title": "Dispute quarantine",
            "blurb": "Accepted disputes retire the bad card and mint a "
                     "fresh retry due now.",
            "path": "/due", "anchor": "queue"}
