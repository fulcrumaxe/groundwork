"""Unique HTML <title> per page including context (I-1).

Pure helper for web.page(): keeps the visible H1 as the base title
but appends module summary / lesson name so browser tabs and history
entries are unique. No I/O, no DB access.
"""
from __future__ import annotations

SITE = "Groundwork"


def _clean(value) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return " ".join(value.split())


def page_title(page: str, context: str = "") -> str:
    """Unique <title> text for a page plus optional context.

    Falls back to the site name when both parts are blank.
    """
    base = _clean(page)
    extra = _clean(context)
    if base and extra:
        return f"{base} — {extra} | {SITE}"
    if base:
        return f"{base} | {SITE}"
    if extra:
        return f"{extra} | {SITE}"
    return SITE
