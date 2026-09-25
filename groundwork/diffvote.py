"""Per-lesson difficulty votes: too easy, just right, too hard (I-145).

Learners tap one of three buttons under each lesson; the aggregate
badge shows the plurality verdict. Votes are categorical — the
tally keeps the full distribution (I-146 weights exercise-type
selection off it) instead of a false-precision mean. record()
validates concept + vote; tallies() batches counts for a module
page; block_html() renders badge plus form. Empty tallies render
the form with a no-votes note (legacy fallback: no badge markup).
Follows the clarity.py vote shape; never raises from renderers.
"""
from __future__ import annotations

import html

from . import db as dbmod

STATUS_ANCHOR = "status-b23-diffvote"

VALID = ("easy", "just", "hard")

_VERDICTS = {"easy": "Too easy", "just": "Just right", "hard": "Too hard"}


def normalize_vote(value) -> str:
    """easy|just|hard for known synonyms; "" fails closed."""
    try:
        v = str(value or "").strip().lower()
    except Exception:  # noqa: BLE001 -- votes must never raise
        return ""
    if v in ("easy", "too easy", "too-easy", "e"):
        return "easy"
    if v in ("just", "just right", "just-right", "j"):
        return "just"
    if v in ("hard", "too hard", "too-hard", "h"):
        return "hard"
    return ""


def record(db_path: str, concept_id: str, vote) -> dict:
    """Store one difficulty vote; errors stay explicit, never silent."""
    norm = normalize_vote(vote)
    if not norm:
        return {"error": "vote must be easy, just, or hard"}
    con = dbmod.connect(db_path)
    try:
        me = con.execute("SELECT concepts.module_id AS mid FROM concepts"
                         " WHERE id=?", (concept_id,)).fetchone()
        if me is None:
            return {"error": "unknown concept"}
        con.execute("INSERT INTO diffvote_votes(concept_id, vote)"
                    " VALUES(?, ?)", (concept_id, norm))
        con.commit()
        return {"vote_id": con.execute(
            "SELECT last_insert_rowid()").fetchone()[0],
            "module_id": me["mid"]}
    finally:
        con.close()


def tallies(db_path: str, cids: list) -> dict:
    """{concept_id: {easy, just, hard}} for a module's concepts."""
    out = {c: {"easy": 0, "just": 0, "hard": 0} for c in cids}
    if not cids:
        return out
    con = dbmod.connect(db_path)
    try:
        rows = con.execute(
            "SELECT concept_id, vote, COUNT(*) AS n"
            " FROM diffvote_votes"
            f" WHERE concept_id IN ({','.join('?' * len(cids))})"
            " GROUP BY concept_id, vote", cids).fetchall()
    finally:
        con.close()
    for r in rows:
        if r["concept_id"] in out and r["vote"] in VALID:
            out[r["concept_id"]][r["vote"]] = r["n"] or 0
    return out


def total(tally: dict) -> int:
    """Vote count in one tally; hostile input reads as zero."""
    try:
        return sum(int(tally.get(v, 0) or 0) for v in VALID)
    except (TypeError, ValueError, AttributeError):
        return 0


def verdict(tally: dict) -> str:
    """Plurality verdict; ties read Mixed, empty reads no-votes."""
    try:
        counts = {v: int(tally.get(v, 0) or 0) for v in VALID}
    except (TypeError, ValueError, AttributeError):
        return "No difficulty votes yet"
    n = sum(counts.values())
    if n == 0:
        return "No difficulty votes yet"
    top = max(counts.values())
    winners = [v for v in VALID if counts[v] == top]
    if len(winners) > 1:
        return "Mixed"
    return _VERDICTS[winners[0]]


def badge_html(tally: dict) -> str:
    """One-line aggregate verdict; "" when no votes (legacy fallback)."""
    try:
        if total(tally) == 0:
            return ""
        parts = [f"{_VERDICTS[v]} {int(tally.get(v, 0) or 0)}"
                 for v in VALID]
        return (f"<p class='diffvote-badge'><small>Difficulty: "
                f"{html.escape(verdict(tally))} "
                f"({' · '.join(parts)})</small></p>")
    except Exception:  # noqa: BLE001 -- badge must never raise
        return ""


def vote_form_html(cid: str, origin: str) -> str:
    """Three-button difficulty vote form for one lesson."""
    try:
        if not isinstance(cid, str) or not cid:
            return ""
        opts = "".join(
            f"<button name='vote' value='{v}'>{_VERDICTS[v]}</button>"
            for v in VALID)
        return (
            f"<form method='post' action='/concepts/{html.escape(cid)}/diffvote'>"
            f"<input type='hidden' name='origin' value='{html.escape(origin)}'>"
            f"{opts}</form>")
    except Exception:  # noqa: BLE001 -- form must never raise
        return ""


def block_html(cid: str, tally: dict, origin: str,
               anchor: bool = False) -> str:
    """Badge plus vote form for one lesson."""
    try:
        mark = " id='diffvote'" if anchor else ""
        badge = badge_html(tally)
        note = "" if badge else "<p><small>No difficulty votes yet</small></p>"
        return (f"<div{mark} class='diffvote'>{badge}{note}"
                f"{vote_form_html(cid, origin)}</div>")
    except Exception:  # noqa: BLE001 -- block must never raise
        return ""


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Difficulty votes "
            "<small>(improvement)</small></h3>"
            "<p>Too easy, just right, or too hard — "
            "<code>groundwork/diffvote.py</code> puts a three-way vote "
            "under every lesson and badges the plurality verdict "
            "(categorical counts, never a mean).</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Difficulty votes</h3>"
                "<p>Difficulty-vote help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "difficulty-vote",
        "kind": "improvement",
        "title": "Vote lesson difficulty",
        "blurb": ("Too easy, just right, or too hard — one tap teaches "
                  "the author."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
