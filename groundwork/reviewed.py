"""Per-lesson "mark as reviewed" without answering (I-17).

Re-read tick for learners revisiting a lesson: a small control beside
each concept that records a private "reviewed" mark without submitting
an answer, grading anything, or touching scheduling.

Design: fully stateless and browser-local. The mark lives in
``localStorage`` under a per-concept key, so no DB table, no schema
change, and no new POST route are needed. This deliberately does NOT
reuse ``known_skips``: a skip is an auditable scheduling claim ("verify
me in 30 days, push my cards out"), while a re-read tick claims
nothing and must not move any due date or write a verification row.

Pure functions, stdlib only (``html``, ``re``). Web wiring lives in
web.py (see WIRES); this module only builds strings the handler embeds.
"""
from __future__ import annotations

import html
import re

KEY_PREFIX = "gw-reviewed:"

_ANCHOR_OK = re.compile(r"[A-Za-z0-9_-]+")

MARK_LABEL = "Mark as reviewed"
MARKED_LABEL = "Reviewed ✓"


def _slug(value) -> str:
    """Safe key slug: alphanumerics plus _-, capped at 64 chars."""
    if value is None:
        text = "unknown"
    else:
        text = value if isinstance(value, str) else str(value)
    slug = "".join(_ANCHOR_OK.findall(text.strip()))[:64] or "unknown"
    return slug


def storage_key(concept_id) -> str:
    """localStorage key for one concept's reviewed mark."""
    return KEY_PREFIX + _slug(concept_id)


def is_marked_html(concept_id) -> str:
    """Placeholder span hydrated by script_js() into the marked state."""
    return (
        f"<span data-reviewed-mark='{html.escape(_slug(concept_id), quote=True)}' "
        f"data-reviewed-key='{html.escape(storage_key(concept_id), quote=True)}'>"
        "</span>"
    )


def mark_control(concept_id, anchor: bool = False) -> str:
    """Per-lesson control: button + placeholder span, no form/POST.

    The first concept on the page may take ``anchor=True`` so the tour
    can target it; the Status-page home keeps the canonical
    ``status-b7-reviewed`` id (see section_html).
    """
    mark = " id='reviewed-mark'" if anchor else ""
    slug = _slug(concept_id)
    key = storage_key(concept_id)
    return (
        f"<p{mark} class='reviewed-control' "
        f"data-reviewed-key='{html.escape(key, quote=True)}'>"
        f"<button type='button' data-reviewed-btn='{html.escape(slug, quote=True)}'>"
        f"{html.escape(MARK_LABEL)}</button>"
        f"<small data-reviewed-state='{html.escape(slug, quote=True)}'>"
        "Re-reading? Tick this — no answer, no grade, stays in your browser."
        "</small></p>"
    )


def script_js() -> str:
    """Hydrate marks from localStorage; toggle on click. No navigation."""
    return (
        "<script>(function(){"
        "function get(k){try{return localStorage.getItem(k);}catch(e){return null;}}"
        "function set(k,v){try{localStorage.setItem(k,'1');}catch(e){}}"
        "function del(k){try{localStorage.removeItem(k);}catch(e){}}"
        "function paint(btn,state,on){"
        f"btn.textContent=on?{MARKED_LABEL!r}:{MARK_LABEL!r};"
        "state.textContent=on?"
        "'Reviewed — stored only in this browser. Click again to clear.'"
        ":'Re-reading? Tick this — no answer, no grade, stays in your browser.';}"
        "Array.prototype.forEach.call("
        "document.querySelectorAll('.reviewed-control'),function(p){"
        "var k=p.getAttribute('data-reviewed-key');"
        "var btn=p.querySelector('[data-reviewed-btn]');"
        "var state=p.querySelector('[data-reviewed-state]');"
        "if(!k||!btn||!state)return;"
        "paint(btn,state,get(k)==='1');"
        "btn.addEventListener('click',function(){"
        "var on=get(k)==='1';"
        "if(on){del(k);}else{set(k,'1');}"
        "paint(btn,state,!on);});});})();</script>"
    )


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        "<h2 id='status-b7-reviewed'>Mark as reviewed</h2>"
        "<p>Re-reading a lesson ticks it without answering: a per-lesson "
        "button stores a private mark in <code>localStorage</code> "
        f"(<code>{html.escape(KEY_PREFIX)}&lt;concept&gt;</code>) — no grade, "
        "no scheduling change, no database write. "
        "Unlike Already-know it never touches <code>known_skips</code> "
        "or moves a due date. "
        "<code>groundwork/reviewed.py</code>.</p>"
    )
