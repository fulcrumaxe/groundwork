"""Grade disputes: learners flag wrong references with one click (I-193).

A dispute records the card, the learner's reason, and a maintainer
verdict (open/accepted/rejected). Accepted disputes are reviewed by
maintainers — quarantining and regeneration ride in I-195, not here.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import sched as schedmod

OPEN = "open"
VERDICTS = ("accepted", "rejected")


def open_dispute(db_path: str, card_id: str, reason: str) -> dict:
    """File a dispute; unknown cards and empty reasons are refused."""
    reason = (reason or "").strip()[:2000]
    if not reason:
        return {"error": "a reason is required"}
    con = dbmod.connect(db_path)
    try:
        row = con.execute("SELECT concepts.module_id AS mid FROM cards"
                          " JOIN concepts ON concepts.id = cards.concept_id"
                          " WHERE cards.id=?", (card_id,)).fetchone()
        if row is None:
            return {"error": "unknown card"}
        cur = con.execute(
            "INSERT INTO disputes(card_id, reason, status, created_at)"
            " VALUES(?,?,?,?)",
            (card_id, reason, OPEN, schedmod.iso(schedmod.utcnow())))
        con.commit()
        return {"dispute_id": cur.lastrowid, "status": OPEN}
    finally:
        con.close()


def list_disputes(db_path: str, status: str = OPEN) -> list[dict]:
    """Open disputes (default) with card and module context."""
    con = dbmod.connect(db_path)
    try:
        rows = con.execute(
            "SELECT disputes.id, disputes.card_id, disputes.reason,"
            " disputes.status, disputes.created_at,"
            " concepts.name AS concept, concepts.module_id AS module_id"
            " FROM disputes JOIN cards ON cards.id = disputes.card_id"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE disputes.status=? ORDER BY disputes.id",
            (status,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def resolve_dispute(db_path: str, dispute_id: int, verdict: str) -> dict:
    """Maintainer verdict; only accepted/rejected land."""
    if verdict not in VERDICTS:
        return {"error": "verdict must be accepted or rejected"}
    con = dbmod.connect(db_path)
    try:
        cur = con.execute("UPDATE disputes SET status=? WHERE id=?",
                          (verdict, dispute_id))
        con.commit()
        if cur.rowcount == 0:
            return {"error": "unknown dispute"}
        return {"dispute_id": dispute_id, "status": verdict}
    finally:
        con.close()


def dispute_form_html(card_id: str, origin: str = "/due") -> str:
    """One-click dispute box beneath a card's answer area."""
    return (
        f"<details><summary>Dispute this grade</summary>"
        f"<form method='post' action='/cards/{html.escape(card_id)}/dispute'>"
        f"<input type='hidden' name='origin' "
        f"value='{html.escape(origin, quote=True)}'>"
        f"<label>What is wrong with the reference?<br>"
        f"<input name='reason' size='50' "
        f"placeholder='The reference answer is wrong because…'></label> "
        f"<button>File dispute</button></form></details>")


def queue_html(db_path: str) -> str:
    """Maintainer queue: open disputes with accept/reject actions."""
    open_rows = list_disputes(db_path, OPEN)
    if not open_rows:
        return ("<p>No open disputes. Wrong references get fixed here — "
                "file one from any card.</p>")
    items = []
    for d in open_rows:
        items.append(
            f"<p><b>#{d['id']}</b> {html.escape(d['concept'] or '')} "
            f"(<a href='/modules/{d['module_id']}'>module</a>) — "
            f"{html.escape(d['reason'] or '')}<br>"
            f"<form method='post' action='/disputes/{d['id']}/resolve' "
            f"style='display:inline'>"
            f"<button name='verdict' value='accepted'>Accept</button>"
            f"<button name='verdict' value='rejected'>Reject</button>"
            f"</form></p>")
    return "".join(items)
