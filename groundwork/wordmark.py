"""Wordmark/logo: inline SVG mark for header and module exports (I-55).

One small vector lockup — a rounded-square "G" monogram plus the word
"Groundwork" — rendered inline so it needs no image file, no webfont,
and no network. Every painted shape uses currentColor, so the mark
inherits the surrounding text color and adapts to palettes including
dark mode with zero theme code. Heights clamp to 16-32px, where the
chunky monogram plus short word stay legible. Pure functions, stdlib
only, no I/O, no DB.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b10-wordmark"

WORD = "Groundwork"
MIN_HEIGHT = 16
DEFAULT_HEIGHT = 24
MAX_HEIGHT = 32

# viewBox for the full lockup: 32px monogram + word set to its right.
_VIEWBOX = "0 0 168 32"
# Offline-safe stacks (mirror fontstack.py): serif G, sans word.
_G_SERIF = ("Georgia,'Palatino Linotype',Palatino,'Book Antiqua',"
            "'DejaVu Serif',serif")
_WORD_SANS = ("'Segoe UI',Roboto,'Helvetica Neue',Arial,'DejaVu Sans',"
              "sans-serif")


def _height(value) -> int:
    """Clamp a requested height into 16-32px; fail closed to 24."""
    try:
        h = int(value)
    except (TypeError, ValueError):
        return DEFAULT_HEIGHT
    if h < MIN_HEIGHT:
        return MIN_HEIGHT
    if h > MAX_HEIGHT:
        return MAX_HEIGHT
    return h


def _word(value) -> str:
    """Coerce the word next to the monogram; fail closed to 'Groundwork'."""
    try:
        if not isinstance(value, str):
            return WORD
        text = value.strip()
    except Exception:  # noqa: BLE001 — renderer never raises
        return WORD
    return text or WORD


def wordmark_svg(height=DEFAULT_HEIGHT, word=WORD) -> str:
    """Return the inline SVG wordmark string; never raises.

    currentColor throughout so the mark adapts to palettes incl. dark
    mode. Vector monogram + short word stay legible at 16-32px heights.
    No emoji anywhere. Bad input fails closed to the default mark.
    """
    try:
        h = _height(height)
        label = _word(word)
        safe = html.escape(label, quote=True)
        return (
            f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='{_VIEWBOX}' "
            f"height='{h}' role='img' aria-label='{safe}' "
            "class='wordmark'>"
            f"<title>{safe}</title>"
            "<rect x='2' y='2' width='28' height='28' rx='7' fill='none' "
            "stroke='currentColor' stroke-width='2.5'/>"
            "<text x='16' y='23.5' font-size='19' text-anchor='middle' "
            f"fill='currentColor' font-family='{_G_SERIF}'>G</text>"
            "<text x='38' y='22' font-size='17' "
            f"fill='currentColor' font-family='{_WORD_SANS}'>{safe}</text>"
            "</svg>"
        )
    except Exception:  # noqa: BLE001 — fail closed, never raise
        return (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 168 32' "
            "height='24' role='img' aria-label='Groundwork' "
            "class='wordmark'><title>Groundwork</title>"
            "<rect x='2' y='2' width='28' height='28' rx='7' fill='none' "
            "stroke='currentColor' stroke-width='2.5'/>"
            "<text x='16' y='23.5' font-size='19' text-anchor='middle' "
            f"fill='currentColor' font-family='{_G_SERIF}'>G</text>"
            "<text x='38' y='22' font-size='17' "
            f"fill='currentColor' font-family='{_WORD_SANS}'>Groundwork</text>"
            "</svg>"
        )


def wordmark_css() -> str:
    """Raw CSS declarations for sizing/spacing; never emits <style> tags.

    The parent wires this string into the head wire alongside the other
    area-module css() output.
    """
    return (
        ".wordmark{height:24px;width:auto;vertical-align:-5px}"
        ".wordmark-sm{height:16px;width:auto;vertical-align:-3px}"
        ".wordmark-lg{height:32px;width:auto;vertical-align:-7px}"
        ".page-head .wordmark{margin-right:.5rem}"
    )


def section_html() -> str:
    """Anchored status subsection showing the mark; wired in by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Wordmark <small>(improvement)</small></h3>"
        f"<p>{wordmark_svg()} A single inline SVG lockup — rounded-square "
        "'G' monogram plus the word Groundwork — painted entirely in "
        "<code>currentColor</code>, so it inherits the palette and adapts "
        "to dark mode with no extra code. No image file, no webfont, no "
        "network, no emoji. <code>groundwork/wordmark.py</code> provides "
        "<code>wordmark_svg()</code> (height clamped to 16-32px, fails "
        "closed, never raises) and <code>wordmark_css()</code> (raw "
        "sizing/spacing declarations for the head wire).</p>"
    )
