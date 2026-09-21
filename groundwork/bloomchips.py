"""Per-tier Bloom chip colors for cards, History, and coach table (I-56).

Every Bloom tier gets its own chip color so a card's skill tier reads at
a glance in the review queue, the History attempt list, and the
calibration coach table. All three surfaces share one hook —
`<span class='chip bloom-<tier>'>` built by chip_html()/chip_class() —
and chip_css() colors that hook. Dark mode re-assigns the same
--bloom-* tokens (the darkmode.py shape), so each tier rule follows
both palettes with no selector duplication. Pure functions, stdlib
only, no I/O, no DB or schema changes, no web.py edits.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b10-bloomchips"

BLOOM_TIERS = (
    "recall",
    "explain",
    "apply",
    "analyse",
    "modify",
    "evaluate",
    "create",
)

# Keys match pipeline.BLOOM_DEFAULT_TYPES exactly. Each tier carries
# a light background/foreground pair plus a dark pair; light grounds
# take dark text, dark grounds take near-white text, so chips stay
# readable under both palettes.
BLOOM_COLORS = {
    "recall": {"bg": "#e3f2e8", "fg": "#0b4d2e",
               "dark_bg": "#0b4d2e", "dark_fg": "#d3f0dd"},
    "explain": {"bg": "#e0f0f5", "fg": "#0c4a5e",
                "dark_bg": "#0c4a5e", "dark_fg": "#cdeff7"},
    "apply": {"bg": "#e2e9fb", "fg": "#1e3a8a",
              "dark_bg": "#1e3a8a", "dark_fg": "#dbe4fd"},
    "analyse": {"bg": "#ece5f8", "fg": "#4c1d95",
                "dark_bg": "#4c1d95", "dark_fg": "#e6dcfa"},
    "modify": {"bg": "#fbe7ef", "fg": "#831843",
               "dark_bg": "#831843", "dark_fg": "#f9d3e0"},
    "evaluate": {"bg": "#fdf0dc", "fg": "#7c2d12",
                 "dark_bg": "#7c2d12", "dark_fg": "#fbe3c8"},
    "create": {"bg": "#faf3c8", "fg": "#713f12",
               "dark_bg": "#713f12", "dark_fg": "#faf0c0"},
}

_NEUTRAL = {"bg": "#e8e8e8", "fg": "#1a1a1a",
            "dark_bg": "#2a2a2a", "dark_fg": "#ececec"}


def tier_key(tier) -> str:
    """Normalized tier name, or "" when unknown; never raises."""
    try:
        key = str(tier).strip().lower()
        return key if key in BLOOM_COLORS else ""
    except Exception:  # noqa: BLE001 — lookup must never raise
        return ""


def color_for(tier) -> dict:
    """Light/dark color entry for a tier; neutral grey when unknown."""
    key = tier_key(tier)
    if not key:
        return dict(_NEUTRAL)
    try:
        return dict(BLOOM_COLORS[key])
    except Exception:  # noqa: BLE001 — fail closed, never raise
        return dict(_NEUTRAL)


def chip_class(tier) -> str:
    """Chip class hook for a tier; plain 'chip' when unknown."""
    key = tier_key(tier)
    if not key:
        return "chip"
    return f"chip bloom-{key}"


def chip_html(tier, label=None) -> str:
    """Bloom chip span for cards, History, and the coach table.

    Label falls back to the tier name; unknown tiers render a plain
    chip. Never raises.
    """
    try:
        key = tier_key(tier)
        if isinstance(label, str) and label.strip():
            text = label.strip()
        elif key:
            text = key
        else:
            text = "other"
        cls = chip_class(key) if key else "chip"
        return f"<span class='{cls}'>{html.escape(text)}</span>"
    except Exception:  # noqa: BLE001 — renderers must never raise
        return "<span class='chip'>other</span>"


def chip_css() -> str:
    """Raw CSS declarations coloring each tier's chip; never <style> tags.

    A :root block holds a background (--bloom-<tier>) and foreground
    (--bloom-<tier>-fg) token per tier; one rule per tier references
    only its tokens; a prefers-color-scheme block re-assigns the same
    tokens for dark mode. The parent wires this string into the head
    wire. Text colors are explicit per tier (not var(--ink)) so tinted
    grounds keep contrast under both palettes.
    """
    try:
        light = "".join(
            f"--bloom-{t}:{BLOOM_COLORS[t]['bg']};"
            f"--bloom-{t}-fg:{BLOOM_COLORS[t]['fg']};"
            for t in BLOOM_TIERS)
        rules = "".join(
            f".chip.bloom-{t}{{background:var(--bloom-{t});"
            f"color:var(--bloom-{t}-fg);"
            f"border-color:var(--bloom-{t}-fg)}}"
            for t in BLOOM_TIERS)
        dark = "".join(
            f"--bloom-{t}:{BLOOM_COLORS[t]['dark_bg']};"
            f"--bloom-{t}-fg:{BLOOM_COLORS[t]['dark_fg']};"
            for t in BLOOM_TIERS)
        return (f":root{{{light}}}" + rules +
                "@media (prefers-color-scheme: dark){:root{" + dark + "}}")
    except Exception:  # noqa: BLE001 — CSS helpers must never raise
        return ":root{}"


def tour_entry() -> dict:
    """Feature-tour registry entry for the parent to append."""
    return {"id": "bloom-chip-colors", "kind": "improvement",
            "title": "Bloom chip colors",
            "blurb": "Each Bloom tier has its own chip color in cards, "
                     "History, and the coach table — scan for weak skills "
                     "at a glance.",
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection with a live chip per tier; db-free."""
    try:
        chips = " ".join(chip_html(t) for t in BLOOM_TIERS)
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Bloom chip colors "
            "<small>(improvement)</small></h3>"
            "<p>Every Bloom tier has its own chip color in cards, History, "
            "and the calibration coach table, readable in light and dark "
            f"palettes: {chips} "
            "<code>groundwork/bloomchips.py</code> provides "
            "<code>chip_css()</code> (raw declarations for the head wire — "
            "never style tags) and <code>chip_class()</code>/"
            "<code>chip_html()</code> (fail-closed hooks, plain "
            "<code>chip</code> when the tier is unknown).</p>"
        )
    except Exception:  # noqa: BLE001 — status must always render
        return f"<h3 id='{STATUS_ANCHOR}'>Bloom chip colors</h3>"
