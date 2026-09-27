"""Bonus attempts: practice that never moves FSRS stats (I-192).

A bonus attempt grades exactly like a normal review -- same result,
same feedback -- but persists nothing: no FSRS stability/difficulty
move, no due change, no mastery roll, no reviews row, no banked
points. Because every accuracy aggregate (History calibration, week
counts, north-star delayed accuracy, owned_map attempts) reads the
reviews table, skipping the INSERT excludes bonus attempts from all
of them with no aggregate rewrites and no schema change.

Two classes count as bonus (either suffices):
- probe answers: F-51 retest probes (probe=7|30 extras) are
  retention checks, already detected in-memory as was_probe by
  MCPServer.submit_review; they keep their last_probe stamp so the
  probe cycle still closes.
- explicit bonus: practice-similar variants (I-191) post bonus=1
  with the review form; submit_review takes it as a bonus kwarg.

No DB/schema changes. Legacy callers (no bonus flag, non-probe
cards) persist byte-identical rows to before.
"""
from __future__ import annotations

from urllib.parse import parse_qs

STATUS_ANCHOR = "status-b28-bonus"

#: POST values that mean "this attempt is bonus practice".
TRUTHY = ("1", "true", "yes", "on")


def should_exclude(was_probe=False, bonus=False) -> bool:
    """True when the attempt must skip all stat persistence.

    Either channel suffices: an in-memory probe detection or an
    explicit bonus flag. Anything unreadable fails closed to False
    (persist normally, the legacy behavior); never raises.
    """
    try:
        return bool(was_probe) or bool(bonus)
    except Exception:  # noqa: BLE001 -- exclusion check never raises
        return False


def from_body(raw) -> bool:
    """True when a review POST body carries bonus=1 (or true/yes/on).

    Parsed with parse_qs, so a bonus=1 inside the answer text stays
    an answer -- only a real bonus field counts. Missing/unreadable
    bodies fail closed to False; never raises.
    """
    try:
        if not isinstance(raw, str) or not raw:
            return False
        form = parse_qs(raw, keep_blank_values=True)
        return any(str(v).strip().lower() in TRUTHY
                   for v in form.get("bonus", []))
    except Exception:  # noqa: BLE001 -- form parsing never raises
        return False


def section_html() -> str:
    """Anchored status subsection; joined by the batch28 home module."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Bonus attempts skip stats "
        "<small>(improvement)</small></h3>"
        "<p>Bonus practice grades like a normal review but persists "
        "nothing: no FSRS stability/difficulty move, no due change, no "
        "mastery roll, no reviews row, no banked points. "
        "<code>groundwork/bonus.py</code> owns the rule -- "
        "<code>should_exclude()</code> (probe answers plus explicit "
        "<code>bonus=1</code> variants) with <code>from_body()</code> "
        "parsing the review form. Skipping the INSERT (not a marker "
        "column) is what keeps every reviews-table aggregate -- History "
        "calibration, week counts, north-star accuracy, owned counts -- "
        "clean with no rewrites. Probes keep their "
        "<code>last_probe</code> stamp so the retest cycle still "
        "closes; legacy submits persist byte-identical rows.</p>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "bonus-attempts",
        "kind": "improvement",
        "title": "Bonus attempts skip stats",
        "blurb": "Probe extras and bonus variants grade like normal but move no FSRS state, mastery, or accuracy count.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
