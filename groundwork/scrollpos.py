"""Preserve scroll position when returning from a result screen (I-14).

Answer -> result -> "Continue where you left off" flow: today the
origin is a bare page path ("/due", "/modules/<id>"), so the browser
lands at the top of a long queue instead of the card just answered.
This module adds the missing half with pure functions only:

* per-card anchors (``card-<id>``) appended to the origin, so the
  back link deep-links to the answered card;
* a small sessionStorage helper that saves the exact pixel offset on
  submit and restores it on return (per-tab, per-origin key, so two
  tabs never fight);
* the status subsection for the machine-room page.

No I/O, no DB/schema changes, stdlib only (``html``, ``re``).
Web wiring lives in web.py (see WIRES); this module only builds
strings the handler embeds.
"""
from __future__ import annotations

import html
import re

KEY_PREFIX = "gw-scroll:"

_SAFE_CHUNK = re.compile(r"[A-Za-z0-9_.\-/~?=&;%+]+")
_ANCHOR_OK = re.compile(r"[A-Za-z0-9_-]+")


def safe_path(value) -> str:
    """Keep only a same-site page path; fall back to the Due queue."""
    v = (value or "/")
    if not isinstance(v, str):
        v = str(v)
    v = v.strip().split("#")[0]
    if (v.startswith("/") and not v.startswith("//")
            and "\\" not in v
            and not any(ch.isspace() or ch in "\"'<>`" for ch in v)):
        return v or "/"
    return "/"


def split_origin(origin) -> dict:
    """Split an origin into {"path": ..., "anchor": ...}.

    The path is sanitised like web._safe_origin; the anchor keeps
    only [A-Za-z0-9_-] (anything else is dropped). Never raises.
    """
    if not isinstance(origin, str):
        origin = "" if origin is None else str(origin)
    path, _, frag = origin.partition("#")
    anchor = "".join(_ANCHOR_OK.findall(frag.strip()))[:64]
    return {"path": safe_path(path), "anchor": anchor}


def card_anchor(card_id) -> str:
    """Stable per-card anchor slug, e.g. "card-abc123"."""
    if card_id is None:
        text = "unknown"
    else:
        text = card_id if isinstance(card_id, str) else str(card_id)
    slug = "".join(_ANCHOR_OK.findall(text.strip()))[:48] or "unknown"
    return f"card-{slug}"


def origin_with_anchor(origin, card_id=None) -> str:
    """Origin path carrying the return anchor for one card.

    "/due" + "c9" -> "/due#card-c9". An existing anchor wins over
    card_id; an empty/unsafe origin falls back to "/".
    """
    parts = split_origin(origin)
    anchor = parts["anchor"] or (card_anchor(card_id) if card_id is not None else "")
    if anchor:
        return f"{parts['path']}#{anchor}"
    return parts["path"]


def back_href(origin, card_id=None) -> str:
    """Href the result screen's back link should point at."""
    return origin_with_anchor(origin, card_id)


def origin_field(origin, card_id=None) -> str:
    """Hidden origin input carrying the anchored return target."""
    target = origin_with_anchor(origin, card_id)
    return (f"<input type='hidden' name='origin' "
            f"value='{html.escape(target, quote=True)}'>")


def storage_key(origin) -> str:
    """sessionStorage key for one origin path (anchor-free)."""
    return KEY_PREFIX + split_origin(origin)["path"]


def record_js() -> str:
    """Save scrollY per origin on every card-answer submit."""
    return (
        "<script>(function(){"
        "function key(f){var o=f.querySelector(\"input[name='origin']\");"
        "var v=o&&o.value?o.value.split('#')[0]:location.pathname;"
        "return 'GWSCROLL'.replace('GWSCROLL',\"" + KEY_PREFIX + "\")+v;}"
        "Array.prototype.forEach.call("
        "document.querySelectorAll(\"form[action^='/cards/']\"),"
        "function(f){f.addEventListener('submit',function(){"
        "try{sessionStorage.setItem(key(f),String(window.scrollY||0));}"
        "catch(e){}});});})();</script>"
    )


def restore_js(origin="") -> str:
    """Restore saved scrollY for this origin, else fall back to #anchor."""
    key = storage_key(origin)
    return (
        "<script>(function(){"
        f"var k={key!r};var y=null;"
        "try{y=sessionStorage.getItem(k);}catch(e){}"
        "if(y!==null&&y!==''&&!location.hash){"
        "var n=parseInt(y,10);"
        "if(!isNaN(n)){try{sessionStorage.removeItem(k);}catch(e){}"
        "window.scrollTo(0,n);return;}}"
        "if(location.hash){var t=document.getElementById("
        "location.hash.slice(1));"
        "if(t&&t.scrollIntoView)t.scrollIntoView();}"
        "})();</script>"
    )


def script_js(origin="") -> str:
    """Record + restore pair; embed record on queue pages, restore on results."""
    return record_js() + restore_js(origin)


def result_back_link(origin, card_id=None, label="Continue where you left off") -> str:
    """Back-to-origin link that keeps the caller's scroll anchor."""
    href = back_href(origin, card_id)
    return (f"<a class='btn' href='{html.escape(href, quote=True)}'>"
            f"{html.escape(label)}</a>")


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        "<h2 id='status-b6-scrollpos'>Scroll position kept</h2>"
        "<p>Answering a card remembers where you were: the result "
        "screen's back link carries a per-card anchor "
        "(<code>#card-&lt;id&gt;</code>) and a small script restores "
        "the exact pixel offset from <code>sessionStorage</code>. "
        "No DB change; per-tab keys so parallel queues never fight. "
        "<code>groundwork/scrollpos.py</code>.</p>"
    )
