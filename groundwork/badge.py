"""README badge (F-386): concepts-owned as a live SVG.

Pure renderer over a database path — the web Handler serves it at
/badge.svg so any README can embed it. Numbers come from the same
owned map as the Projects page, so the badge never disagrees.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import ownership as ownmod


def counts(db_path: str) -> tuple:
    """(owned concepts, total concepts) across all modules."""
    con = dbmod.connect(db_path)
    try:
        owned_n, total_n = 0, 0
        for (mid,) in con.execute("SELECT id FROM modules").fetchall():
            omap = ownmod.owned_map(con, mid)
            total_n += len(omap)
            owned_n += sum(1 for _, o in omap.values() if o)
    finally:
        con.close()
    return owned_n, total_n


def badge_svg(db_path: str) -> str:
    """Small shield-style SVG: owned/total concepts."""
    owned_n, total_n = counts(db_path)
    label = f"{owned_n}/{total_n} concepts owned"
    wide = 118 + 6 * len(label)
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{wide}' height='20'>"
        f"<rect width='{wide}' height='20' rx='4' fill='#1a1a1a'/>"
        f"<text x='8' y='14' font-size='11' fill='#fff' "
        f"font-family='sans-serif'>{html.escape(label)}</text></svg>")
