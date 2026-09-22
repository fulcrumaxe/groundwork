"""High-contrast overrides beyond dark mode (I-99).

Dark mode re-assigns palette tokens, but OS high-contrast /
Windows forced-colors users still get washed-out tinted chips,
badges, and thin progress fills. This module owns the two
override blocks: a ``prefers-contrast`` block that strengthens
borders/outlines on the existing hooks (``.chip`` incl.
``.owned-badge``/``.chip.bloom-*``, ``.bar i``,
``#readprogress span``), and a ``forced-colors`` block that maps
those hooks to system colors (``Canvas``/``CanvasText``/
``Highlight``) with ``forced-color-adjust:none`` so fills stay
visible where the platform would otherwise flatten author colors.
Raw declarations only, never ``<style>`` tags; the parent
concatenates this into the head wire next to ``dark_css()``.
Pure functions, stdlib only, no I/O, no DB changes.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b18-contrast"

#: Hooks strengthened by both override blocks. Class names verified
#: against web.py (.chip/.bar), bloomchips.py (.chip.bloom-<tier>),
#: and ownedbadge.py (.owned-badge, always paired with .chip).
CHIP_SELECTORS = (".chip", ".owned-badge")
BAR_SELECTORS = (".bar i", "#readprogress span")


def _join(selectors) -> str:
    """Comma-joined selector list; fails closed to .chip."""
    try:
        parts = [s for s in selectors
                 if isinstance(s, str) and s.strip()]
        return ",".join(parts) if parts else ".chip"
    except Exception:  # noqa: BLE001 -- selector lookup never raises
        return ".chip"


def contrast_css() -> str:
    """Raw high-contrast declarations: prefers-contrast + forced-colors.

    Never emits ``<style>`` tags; the parent wires this into the
    head stylesheet. Never raises.
    """
    try:
        chips = _join(CHIP_SELECTORS)
        bars = _join(BAR_SELECTORS)
        return (
            "@media (prefers-contrast: more){"
            f"{chips}{{border-width:2px;border-color:currentColor}}"
            f"{bars}{{outline:2px solid currentColor;outline-offset:-2px}}"
            "}"
            "@media(forced-colors:active){"
            f"{chips}{{forced-color-adjust:none;background:Canvas;"
            "color:CanvasText;border-color:CanvasText}}"
            f"{bars}{{forced-color-adjust:none;background:Highlight}}"
            ".bar{forced-color-adjust:none;background:Canvas;"
            "border:1px solid CanvasText}"
            "}"
        )
    except Exception:  # noqa: BLE001 -- CSS emitter must never raise
        return ("@media(forced-colors:active){"
                ".chip{forced-color-adjust:none;background:Canvas;"
                "color:CanvasText}}")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>High-contrast mode "
        "<small>(improvement)</small></h3>"
        "<p>High-contrast and forced-colors users keep legible chips, "
        "badges, and progress fills: <code>groundwork/contrast.py</code> "
        "provides <code>contrast_css()</code> (a "
        "<code>prefers-contrast</code> block strengthening borders on "
        "the existing chip/bar hooks plus a <code>forced-colors</code> "
        "block mapping them to <code>Canvas</code>/"
        "<code>CanvasText</code>/<code>Highlight</code> with "
        "<code>forced-color-adjust:none</code>, wired into the head "
        "stylesheet on every page). Raw declarations only, "
        "never raises.</p>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "high-contrast-mode",
        "kind": "improvement",
        "title": "High-contrast mode",
        "blurb": "Chips, badges, and progress bars stay legible under OS high-contrast and forced-colors — system colors, not washed-out tints.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
