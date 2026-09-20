"""Next/previous lesson pager inside each lesson article (I-8).

Pure HTML builders over a module's ordered lesson list — no HTTP, no
DB, no schema changes, stdlib only. The web Handler keeps delegation
lines per lesson section; every pager string here is a pure function
of (entries, index).

Each lesson article is a ``<section id='lesson-{slug}'>`` rendered in
``Handler.module_html`` (groundwork/web.py). This module builds the
small ``<nav class='lesson-pager'>`` of deep links between consecutive
sections so a module reads card by card.
"""
from __future__ import annotations

import html


def _slug(text) -> str:
    """URL-fragment-safe anchor slug (mirrors lessons.slug)."""
    text = text if isinstance(text, str) else str(text or "")
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    out = "-".join(filter(None, out.split("-")))
    return out or "lesson"


def normalize(entries) -> list[dict]:
    """Coerce lesson entries to [{'slug', 'name'}], dropping empties."""
    norm = []
    if not isinstance(entries, (list, tuple)):
        return norm
    for e in entries:
        if isinstance(e, dict):
            raw_slug, name = e.get("slug", ""), e.get("name", "")
        elif isinstance(e, (list, tuple)) and len(e) == 2:
            raw_slug, name = e
        else:
            continue
        name = name if isinstance(name, str) else str(name or "")
        raw = raw_slug if isinstance(raw_slug, str) else str(raw_slug or "")
        if not name.strip():
            continue
        norm.append({"slug": _slug(raw or name), "name": name})
    return norm


def neighbors(slugs, index: int) -> tuple:
    """(prev_index|None, next_index|None) around index in order."""
    if not isinstance(slugs, (list, tuple)) or not isinstance(index, int):
        return (None, None)
    if isinstance(index, bool) or len(slugs) < 2:
        return (None, None)
    if not 0 <= index < len(slugs):
        return (None, None)
    prev_i = index - 1 if index > 0 else None
    next_i = index + 1 if index + 1 < len(slugs) else None
    return (prev_i, next_i)


def pager_html(entries, index: int, first: bool = False) -> str:
    """Prev/next nav between lesson sections; '' when nothing to link.

    Links are deep anchors (``#lesson-{slug}``) so they work with no
    JS. ``first=True`` on the module's opening lesson owns ``id='pager'``
    (the tour target); later pagers carry the class only, keeping ids
    unique down the page.
    """
    norm = normalize(entries)
    if len(norm) < 2 or not isinstance(index, int):
        return ""
    if isinstance(index, bool) or not 0 <= index < len(norm):
        return ""
    prev_i, next_i = neighbors(norm, index)
    if prev_i is None and next_i is None:
        return ""
    bits = []
    if prev_i is not None:
        p = norm[prev_i]
        bits.append(
            f"<a href='#lesson-{html.escape(p['slug'], quote=True)}'"
            f" rel='prev'>\u2190 {html.escape(p['name'])}</a>")
    bits.append(f"<small>Lesson {index + 1} of {len(norm)}</small>")
    if next_i is not None:
        n = norm[next_i]
        bits.append(
            f"<a href='#lesson-{html.escape(n['slug'], quote=True)}'"
            f" rel='next'>{html.escape(n['name'])} \u2192</a>")
    ident = " id='pager'" if first else ""
    return f"<nav class='lesson-pager'{ident}>{' \u00b7 '.join(bits)}</nav>"


def section_slugs(concepts) -> list[dict]:
    """Lesson entries in module order from concept rows.

    Accepts sqlite rows or dicts with 'cid' (or 'id') plus 'name';
    the ``module:node`` prefix is stripped before slugging, matching
    the ``lesson-{slug}`` section ids that module_html renders.
    """
    entries = []
    for row in concepts or []:
        try:
            cid = row["cid"]
        except (KeyError, IndexError, TypeError):
            try:
                cid = row["id"]
            except (KeyError, IndexError, TypeError):
                continue
        try:
            name = row["name"]
        except (KeyError, IndexError, TypeError):
            continue
        if isinstance(cid, str) and ":" in cid:
            cid = cid.split(":", 1)[1]
        entries.append({"slug": _slug(cid), "name": name})
    return normalize(entries)


def section_html(db_path: str = "") -> str:
    """Status section: the lesson pager, honestly footnoted."""
    _ = db_path  # no DB read: the pager is a pure view over sections
    return (
        "<h2 id='status-b6-pager'>Lesson pager</h2>"
        "<p>Each lesson article ends with a previous/next card pager — "
        "deep links to the neighbouring <code>#lesson-{slug}</code> "
        "sections plus a \u201cLesson i of n\u201d position note. "
        "<code>groundwork/pager.py</code>; pure functions, stdlib only, "
        "no schema changes.</p>")
