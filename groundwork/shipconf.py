"""Ship-it confidence meter over diff coverage (F-133).

Release confidence = owned fraction of the newest modules' concepts
(the "release diff"). No new tables: owned rule from
ownership.owned_map, window from modules.created_at. Honest when
thin: no modules renders nothing, an unattempted diff says unknown.
"""
from __future__ import annotations

from . import db as dbmod
from . import ownership as ownmod

STATUS_ANCHOR = "status-b25-shipconf"
WINDOW = 5


def confidence(owned, total):
    """Owned/total as int percent, or None when there is no diff."""
    try:
        o, t = int(owned), int(total)
    except (TypeError, ValueError):
        return None
    if t <= 0 or o < 0:
        return None
    return max(0, min(100, round(100 * o / t)))


def level(pct):
    """Ship label for a percent; None stays unknown."""
    if pct is None:
        return "unknown"
    if pct >= 80:
        return "ship it"
    if pct >= 50:
        return "nearly there"
    return "risky"


def window_counts(db_path, limit=WINDOW):
    """{owned, concepts, attempted, modules} over the N newest modules."""
    try:
        con = dbmod.connect(db_path)
        try:
            mods = con.execute(
                "SELECT id FROM modules ORDER BY created_at DESC LIMIT ?",
                (int(limit),)).fetchall()
            o = n = a = 0
            for m in mods:
                for attempts, owned in ownmod.owned_map(
                        con, m["id"]).values():
                    n += 1
                    a += 1 if attempts else 0
                    o += 1 if owned else 0
            return {"owned": o, "concepts": n, "attempted": a,
                    "modules": len(mods)}
        finally:
            con.close()
    except Exception:  # noqa: BLE001 -- meter never breaks the page
        return {"owned": 0, "concepts": 0, "attempted": 0, "modules": 0}


def meter_html(db_path, limit=WINDOW):
    """Release meter; '' with no modules, 'unknown' with no proof."""
    try:
        c = window_counts(db_path, limit)
        if not c["modules"] or not c["concepts"]:
            return ""
        if not c["attempted"]:
            return ("<p id='ship-confidence'><b>Ship confidence: unknown</b> — "
                    f"no proof yet on the last {c['modules']} session"
                    f"{'s' if c['modules'] != 1 else ''} "
                    f"({c['concepts']} concepts).</p>")
        pct = confidence(c["owned"], c["concepts"])
        return (f"<div class='bar' id='ship-confidence' role='img' aria-label="
                f"'{pct}% ship confidence'><i style='width:{pct}%'></i></div>"
                f"<p><strong>{pct}% ship confidence</strong> — {level(pct)} "
                f"({c['owned']}/{c['concepts']} diff concepts owned).</p>")
    except Exception:  # noqa: BLE001 -- meter never breaks the page
        return ""


def status_section_html():
    """Anchored status subsection; joined by groundwork/batch25.py."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Ship confidence "
            "<small>(feature)</small></h3>"
            "<p>Release confidence is your owned fraction on the newest "
            "sessions' concepts — <code>groundwork/shipconf.py</code> counts "
            "via <code>ownership.owned_map</code>; empty libraries render "
            "nothing and unattempted diffs say unknown, never a fake %.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Ship confidence</h3>"
                "<p>Ship-confidence help temporarily unavailable.</p>")


def tour_entry():
    """Tour registry entry for the ship-it confidence meter."""
    return {"id": "ship-confidence", "kind": "feature",
            "title": "Ship-it confidence meter",
            "blurb": ("Your owned coverage on the latest diff — "
                      "unknown until proven."),
            "path": "/reviews", "anchor": "ship-confidence"}
