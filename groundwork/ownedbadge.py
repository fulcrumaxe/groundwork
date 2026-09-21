"""Celebrate Owned status with a non-emoji badge reveal (I-58).

A calm CSS-keyframes reveal for the Owned chip: one 240ms fade+scale
on a dedicated .owned-badge class, with a small CSS-shape seal drawn
in ::before (border ring only - no emoji, no images, no text glyphs).
Pure functions, stdlib only, no I/O, no DB or schema changes, no
web.py edits. badge_css() returns raw declarations only - the parent
concatenates it into the head wire exactly like fontstack.stack_css().
Helpers fail closed and never raise.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b10-ownedbadge"

REVEAL_MS = 240
_KEYFRAMES = "ownedbadge-reveal"


def _is_owned(status) -> bool:
    """True only for the Owned status word; never raises."""
    try:
        return str(status).strip().lower() == "owned"
    except Exception:  # noqa: BLE001 - status check must never raise
        return False


def badge_class(status) -> str:
    """Chip class for a status word; Owned gains the reveal class.

    Unknown, empty, or non-string input fails closed to the plain
    chip so a caller typo can never break rendering. Never raises.
    """
    try:
        if _is_owned(status):
            return "chip owned-badge"
        return "chip"
    except Exception:  # noqa: BLE001 - lookup must never raise
        return "chip"


def badge_html(status="Owned") -> str:
    """Owned chip HTML with the reveal class; never raises.

    Non-Owned words render as a plain escaped chip. Any failure
    falls back to the Owned end state, which is always safe to show.
    """
    try:
        if _is_owned(status):
            return ("<span class='chip owned-badge' "
                    "data-status='Owned'>Owned</span>")
        label = html.escape(str(status) if status is not None else "",
                            quote=True)
        return f"<span class='chip'>{label or 'Owned'}</span>"
    except Exception:  # noqa: BLE001 - markup must never raise
        return ("<span class='chip owned-badge' "
                "data-status='Owned'>Owned</span>")


def badge_css() -> str:
    """Raw CSS declarations for the badge reveal; NEVER <style> tags.

    One keyframes animation (240ms total motion, under the 300ms
    budget) plus the .owned-badge rule, a CSS-shape seal in
    ::before, and a prefers-reduced-motion override that renders
    the end state instantly. ASCII only - no emoji anywhere.
    """
    try:
        return (
            "@keyframes " + _KEYFRAMES + "{"
            "from{opacity:0;transform:scale(.92)}"
            "to{opacity:1;transform:scale(1)}}"
            ".owned-badge{display:inline-block;"
            "animation:" + _KEYFRAMES + " " + str(REVEAL_MS) + "ms "
            "ease-out both}"
            ".owned-badge::before{content:\"\";display:inline-block;"
            "width:.55em;height:.55em;margin-right:.35em;"
            "border:.14em solid currentColor;border-radius:50%;"
            "vertical-align:baseline}"
            "@media(prefers-reduced-motion:reduce){"
            ".owned-badge{animation:none;opacity:1;transform:none}}"
        )
    except Exception:  # noqa: BLE001 - CSS must never raise
        return ".owned-badge{opacity:1}"


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        sample = badge_html("Owned")
    except Exception:  # noqa: BLE001 - sample must never raise
        sample = "<span class='chip owned-badge'>Owned</span>"
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Owned badge reveal "
        "<small>(improvement)</small></h3>"
        "<p>Newly Owned concepts celebrate with a calm quarter-second "
        "reveal: a 240ms fade+scale on a dedicated badge class, sealed "
        "with a CSS ring - shapes and text only, no emoji. "
        "Reduced-motion users see the end state instantly. "
        f"Live sample: {sample} "
        "<code>groundwork/ownedbadge.py</code> provides "
        "<code>badge_css()</code> (raw declarations for the head wire, "
        "never <code>&lt;style&gt;</code> tags) and "
        "<code>badge_html()</code> (Owned chip markup that fails "
        "closed, never raises).</p>"
    )
