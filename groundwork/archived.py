"""Graceful 'module archived' state for deleted modules (I-38).

Unknown id (never existed) -> keep the errors.py 404. Valid-looking id
whose row is gone (deleted) -> explain + library search + sibling links.
Pure HTML over inputs — no DB, no I/O, no groundwork imports; stdlib html only.
"""
from __future__ import annotations

import html
import re

_MAX_ID_LEN = 64
_MAX_SIBLINGS = 8
# Plausible module id: digits ("12") or slug ("intro-loops", "py_01").
_ARCHIVED_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def is_archived_id(module_id: object) -> bool:
    """Heuristic: does this look like a real id whose row is gone?"""
    if not isinstance(module_id, str):
        return False
    mid = module_id.strip()
    if not mid or len(mid) > _MAX_ID_LEN:
        return False
    if "/" in mid or "?" in mid or "#" in mid or " " in mid:
        return False  # path/query junk -> unknown, keep 404
    if _ARCHIVED_RE.match(mid) is None:
        return False
    if mid.strip(".-_") == "":
        return False
    return True


def _sib_link(sib) -> str:
    if isinstance(sib, dict):
        sid = str(sib.get("id", ""))
        label = str(sib.get("title") or sib.get("task_summary") or sid)
    elif isinstance(sib, (tuple, list)) and len(sib) >= 1:
        sid = str(sib[0])
        label = str(sib[1]) if len(sib) > 1 and sib[1] else sid
    else:
        sid, label = str(sib), str(sib)
    return (f"<li><a href='/modules/{html.escape(sid, quote=True)}'>"
            f"{html.escape(label)}</a></li>")


def archived_html(module_id: str, siblings=()) -> str:
    """Deleted-module notice with search + up to 8 sibling links."""
    safe = html.escape(str(module_id))
    sibs = list(siblings or [])[:_MAX_SIBLINGS]
    if sibs:
        follow = ("<p>Keep going with a sibling module:</p><ul>"
                  + "".join(_sib_link(s) for s in sibs) + "</ul>")
    else:
        follow = ("<p>No sibling modules on file — "
                  "<a href='/modules'>browse the library</a>.</p>")
    return (
        f"<div id='archived'><p>This module <code>{safe}</code> was removed "
        "or archived, so there is nothing to study here.</p>"
        "<p>Search the library for its replacement:</p>"
        "<form method='get' action='/modules'>"
        "<input name='repo' placeholder='project repo path…'>"
        "<button>Find project</button></form>"
        f"{follow}"
        "<p><a href='/modules'>Modules</a> · <a href='/'>Projects</a> · "
        "<a href='/status'>Status</a></p></div>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    demo = archived_html("12", [{"id": "9", "title": "Intro loops"}])
    return (
        "<h3 id='status-b8-archived'>Archived-module notice "
        "<small>(improvement)</small></h3>"
        "<p>Valid-looking module ids whose row is gone get an explanation with "
        "library search and sibling links instead of a bare 404; garbage ids keep "
        "the <code>errors.not_found_html</code> 404. "
        "<code>groundwork/archived.py</code>.</p>"
        f"{demo}")
