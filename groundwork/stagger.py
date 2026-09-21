"""Subtle Due card entrance stagger, CSS only (I-59).

Due cards fade up one after another in small steps instead of popping
in all at once. Implemented as one load-played keyframe plus per-card
animation-delay offsets — a keyframe plays on first paint with no state
toggle, so no script element and no framework are needed. stagger_css()
returns raw declarations only (never a wrapped style element; the
parent concatenates it into the head wire next to fontstack/darkmode).
Each card's own motion is 250ms and the delay cascade caps at 245ms;
a prefers-reduced-motion block switches the motion off. Pure
functions, stdlib only, no I/O.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b10-stagger"

STEP_MS = 35
MAX_CARDS = 8
TOTAL_BUDGET_MS = 300
KEYFRAME_S = 0.25

# due_html() wraps the queue in <div id='queue'>; each module group is
# a <details> whose first child is the <summary>, so card N of a group
# is article:nth-child(N + 1). Targeting the articles needs no markup
# change and leaves the lead-card tour ids (up-next, due-why, ...) alone.
QUEUE = "#queue"
GROUPED_CARD = "#queue details article"


def delay_for(position) -> int:
    """Delay in ms for 1-based card position; fails closed to 0."""
    try:
        pos = int(position)
        if pos < 1:
            return 0
        return min(pos - 1, MAX_CARDS - 1) * STEP_MS
    except Exception:  # noqa: BLE001 — delay lookup must never raise
        return 0


def max_delay_ms() -> int:
    """Largest delay stagger_css() can emit (245ms, under budget)."""
    try:
        return (MAX_CARDS - 1) * STEP_MS
    except Exception:  # noqa: BLE001 — constants must never raise
        return 0


def stagger_css() -> str:
    """Raw CSS declarations for the Due entrance stagger.

    Base keyframe (short rise + fade) plus one nth-child
    animation-delay rule per card slot, a cap rule pinning deeper
    cards to the maximum delay, and a reduced-motion override.
    Raw declarations only — no wrapping tags; never raises.
    """
    try:
        rules = [
            f"{QUEUE} article{{animation:gw-card-in {KEYFRAME_S}s "
            "ease-out both}}",
            "@keyframes gw-card-in{from{opacity:0;transform:translateY(6px)}"
            "to{opacity:1;transform:translateY(0)}}",
        ]
        for pos in range(1, MAX_CARDS + 1):
            rules.append(
                f"{GROUPED_CARD}:nth-child({pos + 1})"
                f"{{animation-delay:{delay_for(pos)}ms}}"
            )
        rules.append(
            f"{GROUPED_CARD}:nth-child(n+{MAX_CARDS + 2})"
            f"{{animation-delay:{max_delay_ms()}ms}}"
        )
        rules.append(
            "@media (prefers-reduced-motion:reduce)"
            f"{{{QUEUE} article{{animation:none}}}}"
        )
        return "".join(rules)
    except Exception:  # noqa: BLE001 — CSS builder must never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Due card stagger <small>(improvement)</small></h3>"
        "<p>Due cards fade up one after another in 35ms steps instead of "
        "appearing all at once — a load-played keyframe with per-card "
        "nth-child <code>animation-delay</code> offsets, capped at 245ms "
        "so the whole stagger stays under 300ms. Pure CSS, no framework "
        "and no scripting; a <code>prefers-reduced-motion</code> override "
        "sets <code>animation:none</code>. <code>groundwork/stagger.py</code> "
        "provides <code>stagger_css()</code> (raw declarations for the head "
        "wire) and <code>delay_for()</code> (per-position delay that fails "
        "closed to 0, never raises).</p>"
    )
