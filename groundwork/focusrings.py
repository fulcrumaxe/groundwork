"""Visible keyboard focus rings everywhere; outlines never removed (I-65).

One comma-grouped :focus-visible rule covers every interactive
selector, so mouse users stay calm and keyboard users always see a
ring. The ring color is not a new hex: --focus-ring references the
existing palette token --accent-history, so darkmode.py's
reassignment flows through with no color fork. The static outline
ring always stays — the reduced-motion override drops only the
transition. Pure functions, stdlib only, no I/O, no DB changes.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b11-focusrings"

RING_COLOR_TOKEN = "--accent-history"  # must stay a key of palette.PALETTE
RING_WIDTH = "3px"
RING_OFFSET = "2px"
TRANSITION_MS = 120
MAX_TRANSITION_MS = 300

SELECTORS = ("a", "button", ".btn", "input", "select", "textarea",
             "summary", ".card-link", "[tabindex]")

_FORBIDDEN = ("outline:none", "outline: none", "outline:0", "outline: 0")


def _str(value) -> str:
    """Fail-closed string coercion; None -> "", never raises."""
    try:
        if value is None:
            return ""
        return value if isinstance(value, str) else str(value)
    except Exception:  # noqa: BLE001 — coercion must never raise
        return ""


def transition_ms(value=TRANSITION_MS) -> int:
    """Transition length clamped to [0, MAX_TRANSITION_MS]; never raises."""
    try:
        if isinstance(value, bool):
            return TRANSITION_MS
        num = int(value)
        return max(0, min(MAX_TRANSITION_MS, num))
    except (TypeError, ValueError):
        return TRANSITION_MS
    except Exception:  # noqa: BLE001 — coercion must never raise
        return TRANSITION_MS


def css(transition: int = TRANSITION_MS) -> str:
    """Raw :focus-visible ring declarations for the head wire.

    NEVER <style> tags here — the parent concatenates the return
    value. No outline:none anywhere: the ring is additive only.
    """
    try:
        ms = transition_ms(transition)
        group = ",".join(f"{s}:focus-visible" for s in SELECTORS)
        root = (":root{--focus-ring:var(--accent-history);"
                "--focus-ring-width:3px;--focus-ring-offset:2px;}")
        ring = (f"{group}{{outline:var(--focus-ring-width) solid "
                "var(--focus-ring);"
                "outline-offset:var(--focus-ring-offset);"
                f"transition:outline-color {ms}ms ease}}")
        calm = (f"@media (prefers-reduced-motion:reduce){{{group}"
                "{transition:none}}}")
        return root + ring + calm
    except Exception:  # noqa: BLE001 — emitter must never raise
        return (":root{--focus-ring:var(--accent-history)}"
                "a:focus-visible{outline:3px solid var(--focus-ring)}")


def covered_selectors(css_text) -> dict:
    """Which SELECTORS carry a :focus-visible rule in the given CSS.

    Returns {"covered": [...], "missing": [...]}; non-string input
    reports everything missing instead of raising.
    """
    try:
        if not isinstance(css_text, str) or not css_text:
            return {"covered": [], "missing": list(SELECTORS)}
        covered = [s for s in SELECTORS if f"{s}:focus-visible" in css_text]
        return {"covered": covered,
                "missing": [s for s in SELECTORS if s not in covered]}
    except Exception:  # noqa: BLE001 — audit must never raise
        return {"covered": [], "missing": list(SELECTORS)}


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Focus-visible rings "
        "<small>(improvement)</small></h3>"
        "<p>Every link, button, field, and card shows one "
        "palette-matched ring the moment you Tab to it — mouse clicks "
        "stay clean, outlines are never deleted, and reduced-motion "
        "users keep the static ring. "
        "<code>groundwork/focusrings.py</code> provides "
        "<code>css()</code> (raw declarations for the head wire, ring "
        "color tied to the palette token) and "
        "<code>covered_selectors()</code> (fail-closed coverage audit).</p>"
    )
