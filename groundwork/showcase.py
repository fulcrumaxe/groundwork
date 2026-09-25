"""Private badge showcase gallery (F-114).

Earned badges in one private place: every owned concept renders
its sealed tile (the ownedbadge seal plus the conceptbadges
emblem), locked concepts stay plain names — no tiers, no rarity,
no public route. The gallery lives on History beside the other
proof sections and always renders (placeholder when empty), so
the anchor never moves. Pure reads over existing tables; never
raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b23-showcase"


def badges(db_path: str) -> list:
    """[{concept, module, owned, attempts}] over all concepts."""
    try:
        from . import db as dbmod
        from . import ownership as ownmod
        con = dbmod.connect(db_path)
        try:
            mods = con.execute(
                "SELECT id FROM modules").fetchall()
            out = []
            for m in mods:
                omap = ownmod.owned_map(con, str(m["id"]))
                names = {r["cid"]: r["name"] for r in con.execute(
                    "SELECT id AS cid, name FROM concepts"
                    " WHERE module_id=?", (str(m["id"]),)).fetchall()}
                for cid, (attempts, owned) in omap.items():
                    out.append({"concept": names.get(cid, cid),
                                "module": str(m["id"]),
                                "owned": bool(owned),
                                "attempts": attempts or 0})
        finally:
            con.close()
        return out
    except Exception:  # noqa: BLE001 -- gallery must never raise
        return []


def gallery_html(db_path: str) -> str:
    """Showcase gallery; placeholder when no badges earned yet."""
    try:
        from . import conceptbadges as cbmod
        from . import ownedbadge as obmod
        tiles = []
        for b in badges(db_path):
            name = html.escape(str(b["concept"]))
            if b["owned"]:
                tiles.append(
                    f"<div class='showcase-tile {obmod.badge_class('Owned')}'>"
                    f"{cbmod.badge_html(b['concept'], True)}"
                    f"<br><small>{name}</small></div>")
            else:
                tiles.append(
                    f"<div class='showcase-tile showcase-locked'>"
                    f"<span class='chip'>{name}</span></div>")
        inner = "".join(tiles) if tiles else (
            "<p>No badges yet — own your first concept and its emblem "
            "lands here, private to you.</p>")
        return (f"<h2 id='showcase'>Badge showcase</h2>{inner}")
    except Exception:  # noqa: BLE001 -- gallery must never raise
        return ("<h2 id='showcase'>Badge showcase</h2>"
                "<p>Showcase temporarily unavailable.</p>")


def showcase_css() -> str:
    """Raw declarations; parent concats into the head wire."""
    try:
        return (".showcase-tile{display:inline-block;margin:.3em;"
                "padding:.4em .6em;border:1px solid currentColor;"
                "border-radius:.5em;text-align:center;vertical-align:top}"
                ".showcase-locked{opacity:.65}")
    except Exception:  # noqa: BLE001 -- CSS emitter must never raise
        return ".showcase-tile{display:inline-block}"


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Badge showcase "
            "<small>(feature)</small></h3>"
            "<p>Your earned badges in one private gallery — "
            "<code>groundwork/showcase.py</code> tiles every owned "
            "concept with its seal and emblem on History (locked "
            "concepts stay plain names; no public route).</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Badge showcase</h3>"
                "<p>Showcase help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "badge-showcase",
        "kind": "feature",
        "title": "Badge showcase",
        "blurb": ("Your earned badges in one private gallery — proof, "
                  "not pressure."),
        "path": "/reviews",
        "anchor": "showcase",
    }
