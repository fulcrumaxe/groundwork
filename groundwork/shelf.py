"""Theme Modules like a library shelf (I-72).

Cover-style cards with a spine accent: every module card
(``<a class='modcard modcard--clickable'>`` built by
``groundwork/clickcards.py`` and embedded by ``web.modules_html``)
grows a left spine bar plus a subtle cover-style elevation, so the
Modules index reads as a shelf of books.

``shelf_css()`` returns raw CSS declarations only, never ``<style>``
tags — the parent concatenates it into the head wire next to
``progbar_css()``. The spine color is a per-module
hook: ``shelf_spine(repo_or_module_id)`` derives a stable hex color
with the exact ``cover.cover_color`` recipe (MD5 -> hue 0-359 ->
HLS at saturation 0.55 / lightness 0.45), so shelf spine and cover
swatch agree for the same repo string. The parent applies it per
card as an inline ``--shelf-spine`` override (see ``spine_decl``);
the stylesheet falls back to ``var(--accent-modules,#8a5a00)`` when
no override is set. A ``prefers-reduced-motion`` override sets
``transition:none`` so reduced-motion users get no lift animation.
Pure functions, stdlib only, no I/O, no DB/schema changes, no
groundwork imports.
"""
from __future__ import annotations

import colorsys
import hashlib
import re

STATUS_ANCHOR = "status-b12-shelf"

SPINE_WIDTH = "6px"
FALLBACK_REPO = "groundwork"
FALLBACK_VAR = "var(--accent-modules,#8a5a00)"

_SATURATION = 0.55
_LIGHTNESS = 0.45

# Real card selectors (groundwork/clickcards.py CARD_CLASS, embedded by
# web.modules_html via clickcardsmod.wrap_card).
SELECTORS = (".modcard", ".modcard--clickable")

_HEX_RE = re.compile(r"^#[0-9a-f]{6}$")


def selectors() -> tuple:
    """Module-card selectors the shelf targets; fails closed, never raises."""
    try:
        if isinstance(SELECTORS, tuple) and all(
                isinstance(s, str) and s.strip() for s in SELECTORS):
            return SELECTORS
        return (".modcard", ".modcard--clickable")
    except Exception:  # noqa: BLE001 — selector lookup must never raise
        return (".modcard", ".modcard--clickable")


def shelf_spine(repo_or_module_id) -> str:
    """Stable spine hex color, e.g. '#3fa9c8'.

    Same recipe as ``cover.cover_color`` (MD5 of the string -> hue ->
    HLS), so the spine and the cover swatch agree for the same repo.
    Non-string or empty input falls back to ``FALLBACK_REPO``; never
    raises, always returns a ``#rrggbb`` string.
    """
    try:
        repo = repo_or_module_id
        if not isinstance(repo, str) or not repo:
            repo = FALLBACK_REPO
        digest = hashlib.md5(repo.encode("utf-8")).hexdigest()
        hue = int(digest[:4], 16) % 360
        r, g, b = colorsys.hls_to_rgb(hue / 360.0, _LIGHTNESS, _SATURATION)
        color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
        if _HEX_RE.match(color):
            return color
        return "#3f8a9c"
    except Exception:  # noqa: BLE001 — color lookup must never raise
        return "#3f8a9c"


def spine_decl(repo_or_module_id) -> str:
    """Inline ``--shelf-spine`` declaration for one card; never raises."""
    try:
        return f"--shelf-spine:{shelf_spine(repo_or_module_id)}"
    except Exception:  # noqa: BLE001 — decl builder must never raise
        return "--shelf-spine:#3f8a9c"


def shelf_css() -> str:
    """Raw CSS declarations: spine accent bar plus cover-style elevation.

    Left spine via ``border-left`` on the real card selectors, with an
    inset ``box-shadow`` echo so the bar survives border-collapsed
    contexts; subtle elevation via a soft drop shadow and a short
    ``box-shadow`` lift transition, gated by a
    ``prefers-reduced-motion`` override to ``transition:none``.
    Never emits ``<style>`` tags; the parent wires this into the head
    stylesheet. Never raises.
    """
    try:
        bar = "".join(
            f"{s}{{border-left:{SPINE_WIDTH} solid var(--shelf-spine,{FALLBACK_VAR});"
            f"box-shadow:inset {SPINE_WIDTH} 0 0 -3px var(--shelf-spine,{FALLBACK_VAR}),"
            "inset 0 1px 0 rgba(255,255,255,.6),0 1px 3px rgba(0,0,0,.12);"
            "transition:box-shadow 150ms ease}}"
            for s in selectors())
        lift = "".join(
            f"{s}:hover{{box-shadow:inset {SPINE_WIDTH} 0 0 -3px "
            f"var(--shelf-spine,{FALLBACK_VAR}),"
            "inset 0 1px 0 rgba(255,255,255,.6),0 4px 12px rgba(0,0,0,.16)}}"
            for s in selectors())
        off = "".join(f"{s}{{transition:none}}" for s in selectors())
        return (bar + lift
                + "@media(prefers-reduced-motion:reduce){"
                + off + "}")
    except Exception:  # noqa: BLE001 — CSS emitter must never raise
        return (".modcard{border-left:6px solid var(--shelf-spine,"
                "var(--accent-modules,#8a5a00));transition:box-shadow 150ms ease}"
                ".modcard--clickable{border-left:6px solid var(--shelf-spine,"
                "var(--accent-modules,#8a5a00));transition:box-shadow 150ms ease}"
                "@media(prefers-reduced-motion:reduce){"
                ".modcard{transition:none}"
                ".modcard--clickable{transition:none}}")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Library shelf <small>(improvement)</small></h3>"
        "<p>Module cards read as a library shelf: a left spine accent bar "
        "via <code>border-left</code> plus an inset shadow echo on the real "
        "card selectors (<code>.modcard</code>, "
        "<code>.modcard--clickable</code>), with a subtle cover-style "
        "elevation and a motion-gated hover lift. The spine color comes "
        "from <code>shelf_spine()</code>, which uses the exact "
        "<code>cover.cover_color</code> recipe (MD5 to hue to HLS) so shelf "
        "and cover agree; the card carries it as an inline "
        "<code>--shelf-spine</code> override. "
        "<code>groundwork/shelf.py</code> provides "
        "<code>shelf_css()</code> (raw declarations only, no "
        "<code>&lt;style&gt;</code> tags — the parent concatenates it into "
        "the head wire) and fail-closed helpers that never raise.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "library-shelf", "kind": "improvement",
            "title": "Library shelf",
            "blurb": "Module cards stand like books on a shelf — a spine accent in each module's own cover color with a subtle lift.",
            "path": "/status", "anchor": "status-b12-shelf"}
