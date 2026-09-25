"""Knowledge-garden view: the repo map blooming as you learn (F-104).

One plot per module, grouped into beds by repo. A module's bloom
stage follows its owned fraction — seed (nothing owned yet), sprout
(some), bloom (all) — so the garden reads as a map of where proof
has taken root. Inline SVG shapes only (no new CSS, no web.py style
wire); data comes from the existing modules/concepts/reviews tables
via ownership.owned_map. No schema change, no new storage.

Caller path (History page, never a Status demo):
``history.history_html`` appends ``section_html`` in both branches.
The section always renders (anchor-stable for the tour); empty
libraries get fallow-bed copy. Never raises.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import ownership as ownmod

STATUS_ANCHOR = "status-b22-knowngarden"

#: Plots drawn before the overflow note takes over; counts stay exact.
MAX_PLOTS = 40

SEED = "seed"
SPROUT = "sprout"
BLOOM = "bloom"


def stage_of(owned, total) -> str:
    """Bloom stage for an owned fraction; hostile input yields seed."""
    try:
        owned_i, total_i = int(owned), int(total)
    except Exception:  # noqa: BLE001 -- staging never raises
        return SEED
    if total_i <= 0 or owned_i <= 0:
        return SEED
    if owned_i >= total_i:
        return BLOOM
    return SPROUT


def plot_html(mid, summary, owned, total) -> str:
    """One SVG plant for one module; hostile input yields "".

    Seed: a dot on soil. Sprout: stem plus two leaves. Bloom: five
    petals around a center. The title names the module with its
    owned fraction; the plot links to the module page.
    """
    try:
        stage = stage_of(owned, total)
        owned_i, total_i = int(owned), int(total)
        link = str(mid or "")
        name = str(summary or link or "module")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""
    try:
        if stage == BLOOM:
            petals = "".join(
                f"<circle cx='{20 + 9 * _cos(i)}' cy='{16 + 9 * _sin(i)}'"
                f" r='5' fill='none' stroke='var(--ink)'/>"
                for i in range(5))
            plant = (f"{petals}<circle cx='20' cy='16' r='4' "
                     "fill='var(--ink)'/>"
                     "<line x1='20' y1='21' x2='20' y2='34' "
                     "stroke='var(--ink)'/>")
        elif stage == SPROUT:
            plant = ("<line x1='20' y1='12' x2='20' y2='34' "
                     "stroke='var(--ink)'/>"
                     "<ellipse cx='14' cy='22' rx='6' ry='3' fill='none' "
                     "stroke='var(--ink)'/>"
                     "<ellipse cx='26' cy='26' rx='6' ry='3' fill='none' "
                     "stroke='var(--ink)'/>")
        else:
            plant = ("<circle cx='20' cy='28' r='3' fill='var(--ink)'/>"
                     "<line x1='8' y1='34' x2='32' y2='34' "
                     "stroke='var(--stale)'/>")
        soil = ("<line x1='8' y1='34' x2='32' y2='34' "
                "stroke='var(--stale)'/>") if stage != SEED else ""
        tip = (f"{name}: {owned_i}/{total_i} owned ({stage})")
        return (
            f"<a href='/modules/{html.escape(link, quote=True)}' "
            f"class='plot {stage}' title='{html.escape(tip, quote=True)}'>"
            f"<svg viewBox='0 0 40 38' width='40' height='38' role='img' "
            f"aria-label='{html.escape(tip, quote=True)}'>{plant}{soil}</svg>"
            f"<br><small>{html.escape(name)}</small></a>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def _cos(i: int) -> float:
    try:
        import math
        return round(math.cos(2 * math.pi * i / 5), 2)
    except Exception:  # noqa: BLE001 -- trig never raises
        return 0.0


def _sin(i: int) -> float:
    try:
        import math
        return round(math.sin(2 * math.pi * i / 5), 2)
    except Exception:  # noqa: BLE001 -- trig never raises
        return 0.0


def garden_stats(db_path: str) -> list:
    """[(repo, mid, summary, owned, total)] oldest-module-first.

    Empty/hostile DB yields []; never raises.
    """
    try:
        con = dbmod.connect(db_path)
        try:
            mods = con.execute(
                "SELECT id, task_summary, repo FROM modules"
                " ORDER BY created_at LIMIT 200").fetchall()
            out = []
            for m in mods:
                omap = ownmod.owned_map(con, m["id"])
                owned = sum(1 for _, o in omap.values() if o)
                out.append((m["repo"] or "shelf", m["id"],
                            m["task_summary"] or m["id"], owned,
                            len(omap)))
        finally:
            con.close()
        return out
    except Exception:  # noqa: BLE001 -- stats never raise
        return []


def beds_for(rows) -> str:
    """Grouped garden beds HTML; []/hostile input yields ""."""
    try:
        rows = list(rows or [])
    except TypeError:
        return ""
    if not rows:
        return ""
    beds: dict[str, list] = {}
    for row in rows:
        try:
            repo, mid, summary, owned, total = row
        except (TypeError, ValueError):
            continue
        beds.setdefault(str(repo or "shelf"), []).append(
            (mid, summary, owned, total))
    parts = []
    for repo in sorted(beds):
        plots = "".join(plot_html(mid, s, o, t)
                        for mid, s, o, t in beds[repo][:MAX_PLOTS])
        if not plots:
            continue
        parts.append(
            f"<h3>{html.escape(repo)}</h3>"
            f"<p class='bed'>{plots}</p>")
    shown = sum(min(len(v), MAX_PLOTS) for v in beds.values())
    total_n = sum(len(v) for v in beds.values())
    if total_n > shown:
        parts.append(f"<p><small>+{total_n - shown} more plots beyond "
                     "the fence.</small></p>")
    return "".join(parts)


def section_html(db_path: str) -> str:
    """Always-rendered History section; the anchor never moves."""
    try:
        beds = beds_for(garden_stats(db_path))
        if not beds:
            beds = ("<p>Fallow beds — your first sprout breaks soil with "
                    "your first owned concept.</p>")
        return f"<h2 id='knowledge-garden'>Knowledge garden</h2>{beds}"
    except Exception:  # noqa: BLE001 -- history never breaks
        return ("<h2 id='knowledge-garden'>Knowledge garden</h2>"
                "<p>Garden temporarily unavailable.</p>")


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        sample = beds_for([("demo", "m1", "adding", 1, 2),
                           ("demo", "m2", "owned-all", 2, 2)])
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Knowledge garden "
            "<small>(feature)</small></h3>"
            "<p>One plot per module, bedded by repo — seed, sprout, or "
            "bloom by owned fraction. <code>groundwork/knowngarden.py"
            "</code> draws inline-SVG plants (no new CSS) from the "
            "existing tables on the History page. A live sample renders "
            "below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Knowledge garden</h3>"
                "<p>Garden help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "knowledge-garden",
        "kind": "feature",
        "title": "Knowledge garden",
        "blurb": ("Your repo map in bloom — every module a plot, every "
                  "owned concept a petal."),
        "path": "/reviews",
        "anchor": "knowledge-garden",
    }
