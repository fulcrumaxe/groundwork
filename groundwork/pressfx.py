"""Sound-free haptic-style press micro-interactions (I-80).

Brief :active scale(0.97) press feedback on the app's REAL buttons
and card actions — the selectors that already exist in web.py /
taptargets.py / clickcards.py (``button``, ``.btn``, submit/button
inputs, ``.card-link``). Pure CSS, no JS, no sound: the base rule
carries a short ``transition:transform`` so both press and release
ease, and the ``:active`` rule applies the scale. Total motion is
PRESS_MS (120ms, well under the 300ms motion budget and the 150ms
press cap); a ``prefers-reduced-motion`` override sets
``transform:none`` + ``transition:none`` so reduced-motion users get
an instant, static press. Focus-visible outlines are untouched —
this module never emits ``outline`` at all, so focusrings.py's rings
stay authoritative. ``pressfx_css()`` returns raw CSS declarations
only, never ``<style>`` tags — the parent concatenates it into the
head wire next to ``progbar_css()``/``stagger_css()``. Pure
functions, stdlib only, no I/O, no DB/schema, no groundwork imports.
"""
from __future__ import annotations

import re

STATUS_ANCHOR = "status-b12-pressfx"

PRESS_MS = 120
MAX_PRESS_MS = 150
SCALE = 0.97

# Every selector below already exists in the rendered app: button and
# .btn / a.btn (web.py base styles, buttons.py primary-left rows,
# taptargets.py tap floor), submit/button inputs (taptargets primary
# selectors), and .card-link (clickcards.py whole-card links).
SELECTORS = ("button", ".btn", "input[type=submit]",
             "input[type=button]", ".card-link")

_DURATION_RE = re.compile(r"(\d+)\s*ms")


def selectors() -> tuple:
    """Press selectors; fails closed to the shipped tuple, never raises."""
    try:
        if isinstance(SELECTORS, tuple) and all(
                isinstance(s, str) and s.strip() for s in SELECTORS):
            return SELECTORS
        return ("button", ".btn", "input[type=submit]",
                "input[type=button]", ".card-link")
    except Exception:  # noqa: BLE001 — selector lookup must never raise
        return ("button", ".btn", "input[type=submit]",
                "input[type=button]", ".card-link")


def duration_ms(value=PRESS_MS) -> int:
    """Clamped press duration in ms (0..MAX_PRESS_MS).

    Non-numeric, negative, boolean, or over-cap input fails closed to
    PRESS_MS; never raises.
    """
    try:
        if isinstance(value, bool):
            return PRESS_MS
        v = int(value)
        if v < 0 or v > MAX_PRESS_MS:
            return PRESS_MS
        return v
    except Exception:  # noqa: BLE001 — duration lookup must never raise
        return PRESS_MS


def pressfx_css() -> str:
    """Raw CSS declarations: press transition + :active scale + reduced-motion off.

    Never emits ``<style>`` tags and never touches ``outline`` — the
    parent wires this into the head stylesheet. Never raises.
    """
    try:
        ms = duration_ms()
        base = ",".join(selectors())
        active = ",".join(f"{s}:active" for s in selectors())
        calm = (f"@media(prefers-reduced-motion:reduce){{{base}"
                "{transform:none;transition:none}}}")
        return (f"{base}{{transition:transform {ms}ms ease}}"
                f"{active}{{transform:scale({SCALE})}}"
                + calm)
    except Exception:  # noqa: BLE001 — CSS emitter must never raise
        return ("button,.btn,input[type=submit],input[type=button],"
                ".card-link{transition:transform 120ms ease}"
                "button:active,.btn:active,input[type=submit]:active,"
                "input[type=button]:active,.card-link:active"
                "{transform:scale(0.97)}"
                "@media(prefers-reduced-motion:reduce){"
                "button,.btn,input[type=submit],input[type=button],"
                ".card-link{transform:none;transition:none}}")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        ms = duration_ms()
    except Exception:  # noqa: BLE001 — status must never raise
        ms = PRESS_MS
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Press micro-interactions <small>(improvement)</small></h3>"
        "<p>Buttons and card actions shrink to "
        f"<code>scale({SCALE})</code> while pressed over "
        f"{ms}ms via <code>transition:transform</code> on the existing selectors "
        "(<code>button</code>, <code>.btn</code>, submit/button inputs, "
        "<code>.card-link</code>) — sound-free haptic-style feedback with no JS. "
        "A <code>prefers-reduced-motion</code> override sets "
        "<code>transform:none;transition:none</code>, and focus outlines are "
        "untouched. <code>groundwork/pressfx.py</code> provides "
        "<code>pressfx_css()</code> (raw declarations only, no "
        "<code>&lt;style&gt;</code> tags — the parent concatenates it into "
        "the head wire) and clamped helpers that fail closed, never raise.</p>"
    )


def tour_entry() -> dict:
    """Tour registry entry for the press micro-interactions."""
    return {"id": "press-micro", "kind": "improvement",
            "title": "Press micro-interactions",
            "blurb": "Buttons and cards press back a touch while you hold them — silent, instant, and still for reduced-motion users.",
            "path": "/status", "anchor": STATUS_ANCHOR}
