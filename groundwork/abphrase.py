"""A/B explainer phrasings, winners kept by delayed recall (I-136).

Half the concepts explain ELI5-first (variant A, the legacy order)
and half explain tradeoffs-first (variant B); assignment is a hash
of the concept id, so there is nothing to store, nothing to leak
across devices, and no schema change. Delayed recall decides: the
first review of a concept studies it, the second and later reviews
recall it, and the variant with the higher recall pass rate leads.
Pure functions over the existing reviews table; never raises.
"""
from __future__ import annotations

import hashlib

from . import db as dbmod

STATUS_ANCHOR = "status-b22-abphrase"

A = "A"
B = "B"


def variant_for(cid) -> str:
    """Deterministic phrasing variant for a concept id.

    md5 bit, so assignment is stable without storage. Hostile or
    blank input is always A (the legacy order). Never raises.
    """
    try:
        text = str(cid or "").strip()
        if not text:
            return A
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()
        return B if int(digest, 16) % 2 else A
    except Exception:  # noqa: BLE001 -- assignment never raises
        return A


def score_variants(attempts) -> dict:
    """{"A": {...}, "B": {...}, "winner": str, "total": int}.

    ``attempts`` is [(cid, grade, reviewed_at)]; per concept the
    earliest review studies and later ones recall (grade >= 4
    passes). Winner is the higher recall rate, "" on ties or no
    recall data. Hostile input yields empty scores; never raises.
    """
    empty = {"A": {"n": 0, "passed": 0, "rate": 0.0},
             "B": {"n": 0, "passed": 0, "rate": 0.0},
             "winner": "", "total": 0}
    try:
        rows = list(attempts or [])
    except TypeError:
        return empty
    try:
        by_concept: dict[str, list] = {}
        for row in rows:
            try:
                cid, grade, when = row
            except (TypeError, ValueError):
                continue
            try:
                g = int(grade or 0)
            except (TypeError, ValueError):
                g = 0
            by_concept.setdefault(str(cid), []).append((str(when or ""),
                                                        g))
        out = {"A": {"n": 0, "passed": 0, "rate": 0.0},
               "B": {"n": 0, "passed": 0, "rate": 0.0},
               "winner": "", "total": 0}
        for cid, tries in by_concept.items():
            ordered = sorted(tries, key=lambda t: t[0])
            for when, g in ordered[1:]:
                v = variant_for(cid)
                out[v]["n"] += 1
                out[v]["passed"] += 1 if g >= 4 else 0
                out["total"] += 1
        for v in ("A", "B"):
            n = out[v]["n"]
            out[v]["rate"] = (out[v]["passed"] / n) if n else 0.0
        if out["A"]["n"] and out["B"]["n"]:
            if out["A"]["rate"] != out["B"]["rate"]:
                out["winner"] = ("A" if out["A"]["rate"] > out["B"]["rate"]
                                 else "B")
        return out
    except Exception:  # noqa: BLE001 -- scoring never raises
        return empty


def variant_report(db_path: str) -> dict:
    """Delayed-recall scoreboard over the whole library. Never raises."""
    try:
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT cards.concept_id AS cid, reviews.grade AS g,"
                " reviews.reviewed_at AS wh FROM reviews"
                " JOIN cards ON cards.id = reviews.card_id"
                " ORDER BY cards.concept_id, reviews.reviewed_at"
                " LIMIT 20000").fetchall()
        finally:
            con.close()
        return score_variants([(r["cid"], r["g"], r["wh"]) for r in rows])
    except Exception:  # noqa: BLE001 -- reports never raise
        return score_variants([])


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        demo = f"add() explains {'tradeoffs' if variant_for('demo:add') == B else 'ELI5'}-first"
        return (
            f"<h3 id='{STATUS_ANCHOR}'>A/B explainer phrasings "
            "<small>(improvement)</small></h3>"
            "<p>Half the concepts lead with the simple story, half with "
            "the tradeoffs — <code>groundwork/abphrase.py</code> assigns "
            "the variant by concept-id hash (no storage) on the lesson "
            "rendering path (<code>lessons.render_levels</code>), and "
            "delayed recall (second-and-later reviews) keeps the winner. "
            f"Sample assignment: {demo}.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>A/B explainer phrasings</h3>"
                "<p>Phrasing help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "ab-phrasings",
        "kind": "improvement",
        "title": "A/B explainer phrasings",
        "blurb": ("Half the lessons lead simple-first, half "
                  "tradeoffs-first — recall keeps the winner."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
