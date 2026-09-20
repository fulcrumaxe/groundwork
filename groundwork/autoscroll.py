"""Auto-scroll the graded verdict into view on the result screen (I-30).

Boundary with scrollpos.py (I-14, shipped): scrollpos owns the
RETURN-to-queue half -- per-card ``#card-<id>`` anchors, the hidden
origin field, and the ``sessionStorage`` ``gw-scroll:<path>`` save /
restore pair (``record_js`` on queue pages, ``restore_js`` on return).
This module owns the RESULT-screen half only: after grading, the
verdict block itself (``id='verdict'``) takes focus and scrolls into
view, honouring ``prefers-reduced-motion``. It never touches
``sessionStorage``, ``gw-scroll``, card anchors, locations, or origins
-- no overlap by construction.

Pure functions only: web.py embeds the returned strings (see WIRES).
No I/O, no DB/schema changes, stdlib only (``html``).
"""
from __future__ import annotations

import html

VERDICT_ID = "verdict"
SCRIPT_MARKER = "data-autoscroll-verdict"
STATUS_ANCHOR = "status-b7-autoscroll"

_VERDICT_P = "<p class='verdict"


def verdict_open(passed: bool) -> str:
    """Opening tag for the verdict block: a focusable anchor target."""
    cls = "ok" if passed else "stale"
    return f"<p class='verdict {cls}' id='{VERDICT_ID}' tabindex='-1'>"


def verdict_block(passed: bool, feedback) -> str:
    """Full verdict paragraph with escaped feedback text."""
    if feedback is None:
        text = ""
    elif isinstance(feedback, str):
        text = feedback
    else:
        text = str(feedback)
    inner = "\u2713 Correct" if passed else "\u2717 Not yet"
    return f"{verdict_open(passed)}{inner} \u2014 {html.escape(text)}</p>"


def enhance_result(body) -> str:
    """Inject the verdict anchor into already-rendered result HTML.

    Adds ``id='verdict' tabindex='-1'`` to the first
    ``<p class='verdict ...'>`` (the shape emitted by
    ``results.render_result``) that lacks an id. Idempotent;
    verdict-free input passes through unchanged; non-string input
    yields ``""``. Never raises.
    """
    if not isinstance(body, str):
        return ""
    if f"id='{VERDICT_ID}'" in body or f'id="{VERDICT_ID}"' in body:
        return body
    head, sep, tail = body.partition(_VERDICT_P)
    if not sep:
        return body
    end = tail.find(">")
    if end == -1:
        return body
    return (head + sep + tail[:end]
            + f" id='{VERDICT_ID}' tabindex='-1'" + tail[end:])


def verdict_js() -> str:
    """Focus + scroll the verdict into view; reduced-motion aware.

    Embed AFTER ``scrollposmod.restore_js(origin)`` so the verdict wins
    on the result screen. Uses no ``sessionStorage`` and no origin keys.
    """
    return (
        f"<script {SCRIPT_MARKER}>"
        "(function(){"
        f"var v=document.getElementById('{VERDICT_ID}');"
        "if(!v)return;"
        "var reduced=false;"
        "try{reduced=window.matchMedia&&window.matchMedia("
        "'(prefers-reduced-motion: reduce)').matches;}catch(e){}"
        "try{v.focus({preventScroll:true});}catch(e){}"
        "if(v.scrollIntoView){v.scrollIntoView("
        "{behavior:reduced?'auto':'smooth',block:'start'});}"
        "})();</script>"
    )


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Result verdict auto-scroll</h3>"
        "<p>After grading, the result screen's verdict block "
        "(<code>id='verdict'</code>) takes focus and scrolls into view, "
        "with <code>prefers-reduced-motion</code> gating the smooth "
        "scroll. Queue-return position stays owned by "
        "<code>groundwork/scrollpos.py</code>; no DB change. "
        "<code>groundwork/autoscroll.py</code>.</p>"
    )
