"""Theme unlocks for milestones, cosmetic only (F-115).

New palettes unlock as proof accumulates: moss at the first
owned concept, dusk at five, canopy with the first teaching
certificate. The gallery renders unlocked swatches (click
applies via :root variables, choice kept in localStorage) and
locked ones greyed with their unlock hint. Purely cosmetic —
the engine, queue, and grades never see it; no-JS keeps the base
theme byte-identical. Reads existing tables only; never raises.
"""
from __future__ import annotations

import html
import json

STATUS_ANCHOR = "status-b23-themeunlock"

PALETTES = (
    {"name": "paper",
     "title": "Paper (base)",
     "vars": {"--ink": "#1a1a1a", "--paper": "#ffffff"},
     "need": "always here"},
    {"name": "moss",
     "title": "Moss",
     "vars": {"--ink": "#1c2b1e", "--paper": "#f2f6ec",
              "--accent-due": "#2c6e31"},
     "need": "own 1 concept"},
    {"name": "dusk",
     "title": "Dusk",
     "vars": {"--ink": "#e8e6df", "--paper": "#23242a",
              "--accent-history": "#9db4d4"},
     "need": "own 5 concepts"},
    {"name": "canopy",
     "title": "Canopy",
     "vars": {"--ink": "#10241a", "--paper": "#e9f2e4",
              "--accent-modules": "#2c6e31"},
     "need": "earn a teaching certificate"},
)


def progress(db_path: str) -> dict:
    """{owned: int, certificates: int} driving unlocks."""
    try:
        from . import db as dbmod
        from . import milestones as milesmod
        from . import teachcert as certmod
        owned = len(milesmod.owned_dates(db_path))
        certs = len(certmod.eligible(db_path))
        return {"owned": owned, "certificates": certs}
    except Exception:  # noqa: BLE001 -- progress must never raise
        return {"owned": 0, "certificates": 0}


def unlocked(db_path: str) -> list:
    """Palettes with locked flags for this library."""
    try:
        prog = progress(db_path)
        out = []
        for p in PALETTES:
            if p["name"] == "paper":
                locked = False
            elif p["name"] == "moss":
                locked = prog["owned"] < 1
            elif p["name"] == "dusk":
                locked = prog["owned"] < 5
            else:
                locked = prog["certificates"] < 1
            out.append({"name": p["name"], "title": p["title"],
                        "vars": dict(p["vars"]), "locked": locked,
                        "need": p["need"]})
        return out
    except Exception:  # noqa: BLE001 -- unlocks must never raise
        return [{"name": "paper", "title": "Paper (base)",
                 "vars": {}, "locked": False, "need": "always here"}]


def gallery_html(db_path: str) -> str:
    """Unlock gallery with apply script; base theme without JS."""
    try:
        bits = []
        for p in unlocked(db_path):
            if p["locked"]:
                bits.append(
                    f"<div class='theme-locked'><span>{html.escape(p['title'])}"
                    f"</span> <small>locked — {html.escape(p['need'])}</small></div>")
            else:
                data = html.escape(json.dumps(p["vars"]))
                bits.append(
                    f"<button class='theme-swatch' data-theme='{p['name']}' "
                    f"data-vars=\"{data}\">{html.escape(p['title'])}</button>")
        return (
            "<h2 id='theme-unlocks'>Theme unlocks</h2>"
            "<div class='theme-gallery'>" + "".join(bits) + "</div>"
            "<script data-themes>"
            "(function(){try{"
            "var key='gw-theme';"
            "function apply(v){try{"
            "var r=document.documentElement;"
            "for(var k in v){r.style.setProperty(k,v[k]);}}catch(e){}}"
            "try{var s=localStorage.getItem(key);"
            "if(s)apply(JSON.parse(s));}catch(e){}"
            "document.querySelectorAll('.theme-swatch').forEach(function(b){"
            "b.addEventListener('click',function(){"
            "try{var v=JSON.parse(b.getAttribute('data-vars'));"
            "localStorage.setItem(key,JSON.stringify(v));apply(v);"
            "}catch(e){}});});"
            "}catch(e){}})</script>")
    except Exception:  # noqa: BLE001 -- gallery must never raise
        return ("<h2 id='theme-unlocks'>Theme unlocks</h2>"
                "<p>Themes temporarily unavailable.</p>")


def theme_css() -> str:
    """Raw declarations; parent concats into the head wire."""
    try:
        return (".theme-gallery{display:flex;gap:.4em;flex-wrap:wrap}"
                ".theme-swatch{padding:.3em .7em;border-radius:999px;"
                "border:1px solid currentColor;background:var(--paper);"
                "color:var(--ink);cursor:pointer}"
                ".theme-locked{opacity:.6}")
    except Exception:  # noqa: BLE001 -- CSS emitter must never raise
        return ".theme-gallery{display:flex}"


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Theme unlocks "
            "<small>(feature)</small></h3>"
            "<p>Milestones earn palettes — "
            "<code>groundwork/themeunlock.py</code> unlocks moss, dusk, "
            "and canopy from owned counts and certificates (cosmetic "
            "only; the choice lives in your browser).</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Theme unlocks</h3>"
                "<p>Theme help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "theme-unlocks",
        "kind": "feature",
        "title": "Theme unlocks",
        "blurb": ("Milestones earn palettes — cosmetic only, kept in "
                  "your browser."),
        "path": "/reviews",
        "anchor": "theme-unlocks",
    }
