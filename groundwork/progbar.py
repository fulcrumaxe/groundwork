"""Animate progress bars with width transitions (I-57).

Width-only transition on the existing progress selectors (module-card
``.bar i`` and reading-bar ``#readprogress span``): both already carry
inline widths, so the transition animates later width changes with no
markup or JS edits. Total motion is TRANSITION_MS (200ms, under the
300ms budget); a ``prefers-reduced-motion`` override sets
``transition:none`` so reduced-motion users get instant jumps.
``progbar_css()`` returns raw CSS declarations only, never ``<style>``
tags — the parent concatenates it into the head wire next to
``stack_css()``/``dark_css()``. Pure functions, stdlib only, no I/O.
"""
from __future__ import annotations

import re

STATUS_ANCHOR = "status-b10-progbar"

TRANSITION_MS = 200
MAX_TRANSITION_MS = 300

SELECTORS = (".bar i", "#readprogress span")

_DURATION_RE = re.compile(r"(\d+)\s*ms")


def selectors() -> tuple:
    """Progress selectors the transition targets; fails closed, never raises."""
    try:
        if isinstance(SELECTORS, tuple) and all(
                isinstance(s, str) and s.strip() for s in SELECTORS):
            return SELECTORS
        return (".bar i", "#readprogress span")
    except Exception:  # noqa: BLE001 — selector lookup must never raise
        return (".bar i", "#readprogress span")


def transition_ms(value=TRANSITION_MS) -> int:
    """Clamped transition duration in ms (0..MAX_TRANSITION_MS).

    Non-numeric, negative, or over-budget input fails closed to
    TRANSITION_MS; never raises.
    """
    try:
        v = int(value)
        if v < 0 or v > MAX_TRANSITION_MS:
            return TRANSITION_MS
        return v
    except Exception:  # noqa: BLE001 — duration lookup must never raise
        return TRANSITION_MS


def progbar_css() -> str:
    """Raw CSS declarations: width transition plus reduced-motion override.

    Never emits ``<style>`` tags; the parent wires this into the head
    stylesheet. Never raises.
    """
    try:
        ms = transition_ms()
        base = "".join(f"{s}{{transition:width {ms}ms ease}}"
                       for s in selectors())
        off = "".join(f"{s}{{transition:none}}" for s in selectors())
        return (base + "@media(prefers-reduced-motion:reduce){"
                + off + "}")
    except Exception:  # noqa: BLE001 — CSS emitter must never raise
        return (".bar i{transition:width 200ms ease}"
                "#readprogress span{transition:width 200ms ease}"
                "@media(prefers-reduced-motion:reduce){"
                ".bar i{transition:none}"
                "#readprogress span{transition:none}}")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        ms = transition_ms()
    except Exception:  # noqa: BLE001 — status must never raise
        ms = TRANSITION_MS
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Progress bar motion <small>(improvement)</small></h3>"
        "<p>Progress fills ease to their new width over "
        f"{ms}ms via <code>transition:width</code> on the existing selectors "
        "(<code>.bar i</code>, <code>#readprogress span</code>), with a "
        "<code>prefers-reduced-motion</code> override that sets "
        "<code>transition:none</code>. <code>groundwork/progbar.py</code> "
        "provides <code>progbar_css()</code> (raw declarations only, no "
        "<code>&lt;style&gt;</code> tags — the parent concatenates it into "
        "the head wire) and clamped helpers that fail closed, never raise.</p>"
    )
