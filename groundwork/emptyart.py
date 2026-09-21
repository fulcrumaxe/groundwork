"""Empty-state illustrations (I-69).

One inline SVG per page that can run dry. Static line art in
``currentColor`` (inherits surrounding text color, works in dark mode
and print), no emoji, no animation elements (motion-safe by
construction: no <animate>, SMIL, CSS keyframes, or JS hooks).
Pure helpers — no I/O, no DB changes. Copy stays single-sourced in
``groundwork/empty.py``; this module only decorates its output.
"""
from __future__ import annotations

from . import empty as emptymod

STATUS_ANCHOR = "status-b11-emptyart"

_CLS = "empty-art"
_OPEN = ("<svg class='{c}' width='64' height='64' viewBox='0 0 64 64' "
         "fill='none' stroke='currentColor' stroke-width='2' "
         "stroke-linecap='round' stroke-linejoin='round' role='img'>")


def _svg(title: str, inner: str) -> str:
    """Wrap inner SVG shapes with a11y title; title is static per page."""
    return _OPEN.format(c=_CLS) + f"<title>{title}</title>{inner}</svg>"


def _due() -> str:
    return _svg("Empty review queue", "<rect x='10' y='18' width='44' height='30' rx='3'/>"
                "<path d='M22 36l8 8 12-16'/>")


def _modules() -> str:
    return _svg("Empty module library", "<rect x='12' y='14' width='16' height='36' rx='2'/>"
                "<rect x='28' y='14' width='16' height='36' rx='2'/>"
                "<path d='M17 22h6M33 22h6'/>")


def _history() -> str:
    return _svg("No attempts yet", "<circle cx='32' cy='34' r='18'/>"
                "<path d='M32 24v10l8 5'/>"
                "<path d='M26 10h12'/>")


def _journal() -> str:
    return _svg("Empty journal", "<path d='M14 44l4-14 20-20 10 10-20 20z'/>"
                "<path d='M36 10l10 10M14 50h36'/>")


def _diagnose() -> str:
    return _svg("Diagnose a traceback", "<circle cx='28' cy='28' r='14'/>"
                "<path d='M38 38l12 12'/>"
                "<path d='M24 28h8M28 24v8'/>")


def _fallback() -> str:
    return _svg("Nothing here yet", "<circle cx='32' cy='32' r='18' stroke-dasharray='5 4'/>"
                "<circle cx='32' cy='32' r='2' fill='currentColor'/>")


_ART = {"due": _due, "modules": _modules, "history": _history,
        "journal": _journal, "diagnose": _diagnose}


def art_for(page: str) -> str:
    """Inline SVG for a page key; neutral fallback for unknown keys."""
    try:
        maker = _ART.get(page, _fallback)
        return maker()
    except Exception:  # noqa: BLE001 — art must never raise
        return _fallback()


def with_art(page: str) -> str:
    """Empty-state markup with art prepended; copy delegated to empty.py."""
    return (f"<figure class='{_CLS}-wrap'>{art_for(page)}"
            f"{emptymod.empty_state(page)}</figure>")


def section_html() -> str:
    """Status section (area module owns it; never web.py)."""
    return ("<h3 id='status-b11-emptyart'>Empty-state illustrations "
            "<small>(improvement)</small></h3>"
            "<p>Every dry page gets one static inline-SVG illustration in "
            "<code>currentColor</code> — no emoji, no motion. "
            "<code>groundwork/emptyart.py</code> provides "
            "<code>art_for()</code> (art per page key plus fallback) and "
            "<code>with_art()</code> (art prepended to "
            "<code>empty.empty_state()</code> output, wording not duplicated).</p>")
