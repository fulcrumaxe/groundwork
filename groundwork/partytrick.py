"""Explain-it party trick from the owned list (F-111).

Sixty seconds, one mastered concept, out loud: the Due page deals
a party trick — a seeded pick over owned concepts (modify/create
pass plus two attempts, the ownership rule) with a study link
back to its lesson. Nothing owned yet renders the locked note
(the anchor never moves); the pick is a pure reorder, never a
scheduler input. Seeded shuffle for variety, deterministic under
test. Stdlib only; never raises.
"""
from __future__ import annotations

import html
import random

STATUS_ANCHOR = "partytrick"


def owned_candidates(con) -> list:
    """Owned [{cid, concept, mid}] ordered by concept name."""
    try:
        from . import ownership as ownmod
        types = ownmod.ownership_types()
        if not types:
            return []
        rows = con.execute(
            "SELECT concepts.id AS cid, concepts.name AS concept,"
            " concepts.module_id AS mid FROM concepts"
            " JOIN cards ON cards.concept_id = concepts.id"
            " JOIN reviews ON reviews.card_id = cards.id"
            f" WHERE cards.exercise_type IN ({','.join('?' * len(types))})"
            " AND reviews.grade >= 4"
            " GROUP BY concepts.id HAVING COUNT(reviews.id) >= 2"
            " ORDER BY concepts.name", types).fetchall()
        return [{"cid": r["cid"], "concept": r["concept"] or r["cid"],
                 "mid": r["mid"]} for r in rows]
    except Exception:  # noqa: BLE001 -- picks must never raise
        return []


def pick(db_path: str, seed=None) -> dict | None:
    """One owned concept (seeded); None when nothing owned."""
    try:
        from . import db as dbmod
        con = dbmod.connect(db_path)
        try:
            cands = owned_candidates(con)
        finally:
            con.close()
        if not cands:
            return None
        rng = random.Random(seed)
        return rng.choice(cands)
    except Exception:  # noqa: BLE001 -- picks must never raise
        return None


def prompt_for(concept: str) -> str:
    """The sixty-second explain-it prompt text."""
    try:
        name = html.escape(str(concept or "this concept"))
        return (f"Sixty seconds, out loud: explain {name} like you are "
                f"teaching it. No notes, no peeking — then check yourself "
                f"against its lesson.")
    except Exception:  # noqa: BLE001 -- prompt must never raise
        return "Sixty seconds, out loud: explain it like teaching."


def section_html(db_path: str, seed=None) -> str:
    """Party-trick section for the Due page; locked note when empty."""
    try:
        from . import lessons as lesmod
        cand = pick(db_path, seed)
        if cand is None:
            return (f"<section id='{STATUS_ANCHOR}'><h2>Party trick</h2>"
                    "<p>No party tricks yet — own your first concept and "
                    "it becomes explain-it material.</p></section>")
        node = str(cand["cid"]).split(":", 1)[-1]
        return (
            f"<section id='{STATUS_ANCHOR}'><h2>Party trick</h2>"
            f"<p>Explain it to me: <a href='/modules/{cand['mid']}"
            f"#lesson-{lesmod.slug(node)}'>"
            f"{html.escape(cand['concept'])}</a></p>"
            f"<p>{prompt_for(cand['concept'])}</p></section>")
    except Exception:  # noqa: BLE001 -- section must never raise
        return (f"<section id='{STATUS_ANCHOR}'><h2>Party trick</h2>"
                "<p>Party tricks temporarily unavailable.</p></section>")


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            "<h3 id='status-b23-partytrick'>Party trick "
            "<small>(feature)</small></h3>"
            "<p>Quiz yourself from your owned list — "
            "<code>groundwork/partytrick.py</code> deals one mastered "
            "concept per Due visit as a sixty-second explain-it prompt "
            "(seeded variety, locked note until the first owned "
            "concept).</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return ("<h3 id='status-b23-partytrick'>Party trick</h3>"
                "<p>Party-trick help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "party-trick",
        "kind": "feature",
        "title": "Explain-it party trick",
        "blurb": ("Quiz yourself from your owned list — explain one "
                  "mastered concept aloud."),
        "path": "/due",
        "anchor": STATUS_ANCHOR,
    }
