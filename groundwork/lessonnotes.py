"""Private lesson notes: per-lesson markdown scratchpad (I-118).

Server renders the box; text lives in browser localStorage under a
per-lesson key — no server DB changes, notes stay private to the device.
"""
from __future__ import annotations

import html


def notes_box(lesson_id) -> str:
    """Notes box HTML; stable id='lessonnotes' anchor."""
    key = lesson_id if isinstance(lesson_id, str) and lesson_id.strip() else "lesson"
    safe = html.escape(key.strip(), quote=True)
    return (
        f"<div id='lessonnotes' data-lesson='{safe}'>"
        "<label>Private notes"
        f"<textarea name='lesson-notes' rows='4' data-notes-for='{safe}'></textarea>"
        "</label>"
        "<script>"
        f"(function(){{var k='gw-notes-{safe}';var t=document.querySelector"
        f"('textarea[data-notes-for=\"{safe}\"]');if(!t)return;"
        "try{t.value=localStorage.getItem(k)||'';}catch(e){}"
        "t.addEventListener('input',function(){try{localStorage.setItem(k,t.value);}catch(e){}});"
        "})();</script></div>"
    )
