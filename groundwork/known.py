"""Already-know skips (I-133): skip the line, verify later.

skip() records the self-certification and pushes the concept's cards
30 days out — the delayed verification. No fake passes are logged:
the skip is its own auditable row, and the cards genuinely come due.
"""
from __future__ import annotations

from datetime import timedelta
import html

from . import db as dbmod
from . import timetag as timetagmod
from . import sched as schedmod

VERIFY_DAYS = 30


def skip(db_path: str, concept_id: str) -> dict:
    """Record an already-know skip and schedule verification."""
    con = dbmod.connect(db_path)
    try:
        me = con.execute("SELECT concepts.module_id AS mid FROM concepts"
                         " WHERE id=?", (concept_id,)).fetchone()
        if me is None:
            return {"error": "unknown concept"}
        verify = schedmod.iso(schedmod.utcnow()
                              + timedelta(days=VERIFY_DAYS))
        con.execute("INSERT INTO known_skips(concept_id, verify_due)"
                    " VALUES(?, ?)", (concept_id, verify))
        con.execute("UPDATE cards SET due=? WHERE concept_id=?"
                    " AND (due IS NULL OR due < ?)",
                    (verify, concept_id, verify))
        con.commit()
        return {"module_id": me["mid"], "verify_due": verify}
    finally:
        con.close()


def pending(db_path: str, cids: list) -> dict:
    """{concept_id: verify_due} for concepts with an open skip."""
    out: dict[str, str] = {}
    if not cids:
        return out
    con = dbmod.connect(db_path)
    try:
        rows = con.execute(
            "SELECT concept_id, MAX(verify_due) AS v FROM known_skips"
            f" WHERE concept_id IN ({','.join('?' * len(cids))})"
            " GROUP BY concept_id", cids).fetchall()
    finally:
        con.close()
    return {r["concept_id"]: r["v"] for r in rows}


def button_html(cid: str, verify_due: str, origin: str,
                anchor: bool = False) -> str:
    """Skip button, or the scheduled verification once skipped."""
    mark = " id='already-know'" if anchor else ""
    if verify_due:
        return (f"<p{mark}><small>Already-knows verified no later than "
                f"{timetagmod.stamp(verify_due)} — the cards come due then."
                f"</small></p>")
    return (
        f"<form{mark} method='post' action='/concepts/{html.escape(cid)}/known'>"
        f"<input type='hidden' name='origin' value='{html.escape(origin)}'>"
        f"<button>Already know this — verify me later</button></form>")
