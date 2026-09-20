"""Recently visited strip on Due (I-24).

Stateless by design: the server renders only an empty container plus
inline scripts — visit history lives in browser ``localStorage`` under
key ``gw-recent`` (capped at 8 entries), so no cookie, DB table, or
schema change is needed. Privacy surface is nil (data never leaves the
device, cleared with site data); works offline; per-browser so shared
machines don't leak trails. With JS off the server renders zero
entries — just the heading and a quiet hint — which is the fallback.

* ``strip_html()`` — Due-page container (``id='recent'``) + render script.
* ``record_js(mid, title)`` — module-page snippet that logs one visit.
* ``clip(entries, limit)`` — pure cap/dedupe helper (mirrors the JS).
* ``section_html()`` — Status-page anchored home (``status-b7-recent``).

Stdlib only (``html``, ``json``). No I/O.
"""
from __future__ import annotations

import html
import json

KEY = "gw-recent"
MAX = 8


def clip(entries, limit: int = MAX) -> list:
    """Most-recent-first, deduped by id, capped at ``limit``. Never raises."""
    try:
        n = int(limit)
    except (TypeError, ValueError):
        n = MAX
    n = max(0, n)
    seen: set = set()
    out: list = []
    items = entries if isinstance(entries, (list, tuple)) else []
    for it in items:
        mid = it.get("id") if isinstance(it, dict) else None
        if not isinstance(mid, str) or not mid.strip() or mid in seen:
            continue
        seen.add(mid)
        out.append(it)
        if len(out) >= n:
            break
    return out


def _safe_js(value: str) -> str:
    """JSON string that cannot close its own <script> block."""
    return json.dumps(value).replace("</", "<\\/")


def strip_html() -> str:
    """Due-page container + renderer. Server emits no entries (JS fills)."""
    return (
        "<section id='recent'><h2>Recently visited</h2>"
        "<p id='recent-empty'>Modules you open will appear here "
        "(kept in this browser only).</p>"
        "<ul id='recent-list'></ul>"
        "<script>(function(){"
        f"var K={KEY!r};var N={MAX};"
        "var ul=document.getElementById('recent-list');if(!ul)return;"
        "var items=[];"
        "try{items=JSON.parse(localStorage.getItem(K)||'[]');}catch(e){items=[];}"
        "if(Object.prototype.toString.call(items)!=='[object Array]')items=[];"
        f"items=items.slice(0,N);"
        "var note=document.getElementById('recent-empty');"
        "items.forEach(function(it){"
        "if(!it||typeof it.id!=='string'||!it.id)return;"
        "var li=document.createElement('li');"
        "var a=document.createElement('a');"
        "a.href='/modules/'+encodeURIComponent(it.id);"
        "a.textContent=(typeof it.title==='string'&&it.title)?it.title:it.id;"
        "li.appendChild(a);ul.appendChild(li);});"
        "if(items.length&&note)note.style.display='none';"
        "})();</script></section>"
    )


def record_js(mid, title: str = "") -> str:
    """Visit-logging snippet for module pages; pushes {id,title,url,ts}."""
    mid_s = mid if isinstance(mid, str) else ("" if mid is None else str(mid))
    title_s = title if isinstance(title, str) else ("" if title is None else str(title))
    return (
        "<script>(function(){"
        f"var K={KEY!r};var N={MAX};"
        f"var mid={_safe_js(mid_s)};var label={_safe_js(title_s)}||mid;"
        "if(!mid)return;"
        "var items=[];"
        "try{items=JSON.parse(localStorage.getItem(K)||'[]');}catch(e){items=[];}"
        "if(Object.prototype.toString.call(items)!=='[object Array]')items=[];"
        "items=items.filter(function(it){return it&&it.id!==mid;});"
        "items.unshift({id:mid,title:label,url:location.pathname,ts:Date.now()});"
        "items=items.slice(0,N);"
        "try{localStorage.setItem(K,JSON.stringify(items));}catch(e){}"
        "})();</script>"
    )


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        "<h2 id='status-b7-recent'>Recently visited strip</h2>"
        "<p>The Due page opens with a recently-visited strip fed only by "
        "browser <code>localStorage</code> (key <code>gw-recent</code>, "
        "capped at 8 entries, rendered with <code>textContent</code> so "
        "titles can't inject markup). No cookie, DB, or schema change; "
        "with JS off the server renders no entries. "
        "<code>groundwork/recent.py</code>.</p>"
    )
