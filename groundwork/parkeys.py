"""Touch-friendly drag plus keyboard reorder for Parsons (I-162).

Wraps parsons.py: same reserve/min-height contract, plus 44px grips
with touch-action:none, roving-tabindex rows (arrows/Home/End move,
one tab stop), and pointer-drag from the grip. Server renders markup;
parkeys_js() only reorders DOM nodes then reuses the existing order
sync, so mouse/touch/keyboard/typed-numbers post one format. Pure
functions, stdlib only (html), no DB, never raise.
"""
from __future__ import annotations

import html

from . import emoji as emojimod
from . import parsons as parsonsmod

GRAB_MIN_PX = 44  # taptargets floor: grip is a full tap target
STATUS_ANCHOR = "status-b25-parkeys"


def _as_list(lines) -> list:
    try:
        return list(lines) if isinstance(lines, (list, tuple)) else []
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return []


def row_html(cid, i, line, n) -> str:
    """One focusable row: roving tabindex, set position, tap buttons."""
    try:
        tab = 0 if i == 0 else -1
        return (f"<li draggable='true' data-i='{i}' tabindex='{tab}' "
                f"aria-posinset='{i + 1}' aria-setsize='{n}' "
                f"aria-label='Line {i + 1} of {n}'>"
                f"<span class='grip pkgrip' aria-hidden='true'></span> "
                f"{html.escape(str(line))} "
                f"{emojimod.move_button('up', cid)}"
                f"{emojimod.move_button('down', cid)}</li>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return f"<li draggable='true' data-i='{i}'>{html.escape(str(line))}</li>"


def list_html(cid, lines, enhanced=True) -> str:
    """Enhanced ol.parkeys; legacy parsons list when off or empty."""
    try:
        rows = _as_list(lines)
        if not enhanced or not rows:
            return parsonsmod.list_html(cid, lines)
        px = parsonsmod.reserve_px(rows)
        items = "".join(row_html(cid, i, l, len(rows))
                        for i, l in enumerate(rows))
        return (f"<ol class='parsons parkeys' id='pl-{cid}' "
                f"style='min-height:{px}px'>{items}</ol>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return parsonsmod.list_html(cid, lines)


def block_html(cid, lines, enhanced=True) -> str:
    """Drop-in for cards.py etype 10/11; legacy bytes when off/empty."""
    try:
        if not enhanced or not _as_list(lines):
            return parsonsmod.block_html(cid, lines)
        return ("<p>Drag the lines into order (or type the numbers):</p>"
                f"{list_html(cid, lines)}"
                f"<input type='hidden' name='answer' id='po-{cid}' value=''>"
                "<label>Order (numbers): <input name='answer_text' size='30' "
                "placeholder='0 1 2 …'></label> ")
    except Exception:  # noqa: BLE001 -- block must never raise
        return parsonsmod.block_html(cid, lines)


def parkeys_css() -> str:
    """Raw declarations (never <style>); head wire concatenates."""
    try:
        return (f"ol.parkeys{{touch-action:pan-y}}"
                f"ol.parkeys .pkgrip{{min-width:{GRAB_MIN_PX}px;"
                f"min-height:{GRAB_MIN_PX}px;touch-action:none;cursor:grab}}"
                "ol.parkeys li:focus{outline:2px solid currentColor;"
                "outline-offset:2px}")
    except Exception:  # noqa: BLE001 -- CSS builder must never raise
        return "ol.parkeys{}"


def parkeys_js() -> str:
    """Arrows/Home/End reorder + grip pointer-drag; reuses parsonsSync."""
    try:
        return ("<script>if(!window.__parkeysInit){window.__parkeysInit=true;"
                "function parkeysSync(ol){if(window.parsonsSync){parsonsSync(ol);return}"
                "var ids=Array.prototype.map.call(ol.querySelectorAll('li'),function(l){return l.getAttribute('data-i')});"
                "document.getElementById('po-'+ol.id.slice(3)).value=ids.join(' ')}"
                "function parkeysRove(ol,on){Array.prototype.forEach.call(ol.querySelectorAll('li'),function(l){l.tabIndex=(l===on?0:-1)})}"
                "function parkeysMove(ol,li,d){var s=(d<0?li.previousElementSibling:li.nextElementSibling);"
                "if(!s)return false;ol.insertBefore(li,(d<0?s:s.nextSibling));return true}"
                "document.addEventListener('DOMContentLoaded',function(){"
                "Array.prototype.forEach.call(document.querySelectorAll('ol.parkeys'),function(ol){"
                "ol.addEventListener('keydown',function(e){var li=e.target.closest('li');if(!li)return;"
                "var k=e.key,m=false;"
                "if(k==='ArrowUp')m=parkeysMove(ol,li,-1);else if(k==='ArrowDown')m=parkeysMove(ol,li,1);"
                "else if(k==='Home'){ol.insertBefore(li,ol.firstChild);m=true}"
                "else if(k==='End'){ol.appendChild(li);m=true}else return;"
                "e.preventDefault();parkeysRove(ol,li);li.focus();if(m)parkeysSync(ol)});"
                "ol.addEventListener('focusin',function(e){var li=e.target.closest('li');if(li)parkeysRove(ol,li)});"
                "var pd=null;"
                "ol.addEventListener('pointerdown',function(e){var g=e.target.closest('.pkgrip');if(!g)return;"
                "pd=g.closest('li');try{ol.setPointerCapture(e.pointerId)}catch(x){}e.preventDefault()});"
                "ol.addEventListener('pointermove',function(e){if(!pd)return;"
                "var el=document.elementFromPoint(e.clientX,e.clientY);var li=(el&&el.closest?el.closest('li'):null);"
                "if(li&&li.parentNode===ol&&li!==pd){var r=li.getBoundingClientRect();"
                "ol.insertBefore(pd,((e.clientY-r.top)>r.height/2?li.nextSibling:li))}e.preventDefault()});"
                "function pdone(){if(pd){parkeysSync(ol);pd=null}}"
                "ol.addEventListener('pointerup',pdone);ol.addEventListener('pointercancel',pdone)})})}</script>")
    except Exception:  # noqa: BLE001 -- script builder must never raise
        return "<script></script>"


def tour_entry() -> dict:
    """Tour registry entry for touch + keyboard Parsons reorder."""
    return {"id": "parsons-touch-keys", "kind": "improvement",
            "title": "Touch + keyboard Parsons reorder",
            "blurb": ("Parsons lists now drag from a fat fingertip grip and "
                      "reorder from the keyboard: Tab in once, then arrows "
                      "move the row. See below."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch25.py."""
    return (f"<h3 id='{STATUS_ANCHOR}'>Touch + keyboard Parsons "
            "<small>(improvement)</small></h3>"
            "<p>Parsons rows carry a 44px <code>.pkgrip</code> "
            "(<code>touch-action:none</code>), roving <code>tabindex</code> "
            "with Arrow/Home/End moves, and pointer-drag; all paths reuse "
            "the existing order sync. <code>groundwork/parkeys.py</code> "
            "delegates to <code>parsons.block_html</code> byte-identically "
            "when off or empty.</p>")
