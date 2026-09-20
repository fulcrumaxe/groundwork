"""Ownership model: which concepts the learner can prove they own.

Owned follows the PRD mastery model: a spaced modify/create pass — a
passing grade on a modify/create card plus a return visit (2+ attempts),
so same-day fluency alone never counts as owned. Shared by the
Projects, Modules, module-detail, and History pages.
"""
from __future__ import annotations

from . import exercises as exmod


def ownership_types() -> list[str]:
    """Exercise types that prove modification skill (modify/create Bloom)."""
    return [str(t) for bloom in ("modify", "create")
            for t in exmod.BLOOM_TYPES.get(bloom, [])]


def owned_map(con, mid: str) -> dict:
    """Per-concept (attempts, owned) for one module."""
    types = ownership_types()
    q = ("SELECT concepts.id AS cid, COUNT(reviews.id) AS attempts,"
         " SUM(CASE WHEN reviews.grade >= 4" +
         (f" AND cards.exercise_type IN ({','.join('?' * len(types))})"
          if types else " AND 0") +
         " THEN 1 ELSE 0 END) AS own_pass"
         " FROM concepts LEFT JOIN cards ON cards.concept_id = concepts.id"
         " LEFT JOIN reviews ON reviews.card_id = cards.id"
         " WHERE concepts.module_id=? GROUP BY concepts.id")
    args = list(types) + [mid] if types else [mid]
    out = {}
    for r in con.execute(q, args).fetchall():
        attempts = r["attempts"] or 0
        out[r["cid"]] = (attempts, bool(r["own_pass"]) and attempts >= 2)
    return out
