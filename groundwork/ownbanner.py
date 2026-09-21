"""Confetti-free celebration: Owned triggers a calm full-width banner (I-79).

A quiet milestone moment for newly Owned concepts: one full-width
``.ownbanner`` block with garden-echo copy ("taken root", seed -> tree)
and the existing Owned chip vocabulary (``chip owned-badge`` from
``groundwork/ownedbadge.py``). Composes with the badge reveal -- it
reuses the badge classes, never redefines their keyframes. At most one
optional <=250ms opacity fade, gated by ``prefers-reduced-motion``.
Pure functions, stdlib only, no groundwork imports, no I/O, no DB or
schema changes. ``ownbanner_css()`` returns raw declarations only --
the parent concatenates it into the head wire exactly like
``progbar.progbar_css()``. Helpers fail closed and never raise.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b12-ownbanner"

FADE_MS = 200
MAX_FADE_MS = 250

_KEYFRAMES = "ownbanner-fade"


def fade_ms(value=FADE_MS) -> int:
    """Clamped fade duration in ms (0..MAX_FADE_MS).

    Non-numeric, negative, or over-budget input fails closed to
    FADE_MS; never raises.
    """
    try:
        v = int(value)
        if v < 0 or v > MAX_FADE_MS:
            return FADE_MS
        return v
    except Exception:  # noqa: BLE001 -- duration lookup must never raise
        return FADE_MS


def ownbanner_html(concept_name="") -> str:
    """Calm full-width Owned banner; never raises.

    Escapes ``concept_name``; empty/non-string input falls back to a
    nameless but still calm end state. Reuses the ``chip owned-badge``
    vocabulary so the existing badge reveal composes inside the
    banner. Copy echoes the garden metaphor (taken root), streak-free.
    No emoji, no animation hooks beyond the CSS fade class.
    """
    try:
        try:
            raw = str(concept_name).strip() if concept_name is not None else ""
        except Exception:  # noqa: BLE001 -- str() must never raise
            raw = ""
        if not isinstance(raw, str):
            raw = ""
        name = html.escape(raw, quote=True)
        if name:
            headline = f"Owned -- {name} has taken root."
        else:
            headline = "Owned -- this concept has taken root."
        return (
            "<div class='ownbanner' role='status'>"
            "<span class='chip owned-badge' data-status='Owned'>Owned</span>"
            f"<p class='ownbanner-text'>{headline} "
            "No confetti, no streaks -- just the milestone.</p>"
            "</div>"
        )
    except Exception:  # noqa: BLE001 -- markup must never raise
        return (
            "<div class='ownbanner' role='status'>"
            "<span class='chip owned-badge' data-status='Owned'>Owned</span>"
            "<p class='ownbanner-text'>Owned -- this concept has taken root.</p>"
            "</div>"
        )


def ownbanner_css() -> str:
    """Raw CSS declarations for the banner; NEVER <style> tags.

    Full-width block layout plus one optional fade (FADE_MS, under the
    250ms budget) and a prefers-reduced-motion override that renders
    the end state instantly. ASCII only -- no emoji anywhere. Never
    redefines the ownedbadge keyframes; composes with them.
    """
    try:
        ms = fade_ms()
        return (
            "@keyframes " + _KEYFRAMES + "{"
            "from{opacity:0}"
            "to{opacity:1}}"
            ".ownbanner{display:block;box-sizing:border-box;width:100%;"
            "border:1px solid var(--ink,#1a1a1a);border-radius:10px;"
            "padding:.75rem 1rem;margin:.75rem 0;background:var(--paper);"
            "color:var(--ink);"
            "animation:" + _KEYFRAMES + " " + str(ms) + "ms ease-out both}"
            ".ownbanner-text{margin:.35rem 0 0}"
            ".ownbanner .owned-badge{margin-right:.5rem}"
            "@media(prefers-reduced-motion:reduce){"
            ".ownbanner{animation:none;opacity:1}}"
        )
    except Exception:  # noqa: BLE001 -- CSS must never raise
        return ".ownbanner{display:block;width:100%;opacity:1}"


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        sample = ownbanner_html("Loops")
    except Exception:  # noqa: BLE001 -- sample must never raise
        sample = "<div class='ownbanner' role='status'>Owned</div>"
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Owned banner <small>(improvement)</small></h3>"
        "<p>Newly Owned concepts trigger a calm full-width banner instead "
        "of confetti: garden-echo copy (taken root, seed to tree), "
        "streak-free, reusing the existing <code>chip owned-badge</code> "
        "vocabulary from <code>groundwork/ownedbadge.py</code> so the badge "
        "reveal composes inside it. At most one optional fade "
        f"({fade_ms()}ms, under the 250ms budget) with a "
        "<code>prefers-reduced-motion</code> override that shows the end "
        "state instantly. "
        f"Live sample: {sample} "
        "<code>groundwork/ownbanner.py</code> provides "
        "<code>ownbanner_html()</code> (escaped name, fail-closed) and "
        "<code>ownbanner_css()</code> (raw declarations for the head wire, "
        "never <code>&lt;style&gt;</code> tags).</p>"
    )


def tour_entry() -> dict:
    """Tour registry entry for the Owned banner; never raises."""
    try:
        return {
            "id": "owned-banner",
            "kind": "improvement",
            "title": "Owned banner",
            "blurb": "Owned concepts get a calm full-width banner -- no confetti, just the milestone.",
            "path": "/status",
            "anchor": STATUS_ANCHOR,
        }
    except Exception:  # noqa: BLE001 -- registry must never raise
        return {
            "id": "owned-banner",
            "kind": "improvement",
            "title": "Owned banner",
            "blurb": "Owned concepts get a calm full-width banner.",
            "path": "/status",
            "anchor": "status-b12-ownbanner",
        }
