"""Page-level breadcrumb trail: Due/Modules/History › Module › Lesson › Card (I-3).

One pure helper renders a server-side HTML trail from (label, href)
segments. No I/O, no DB changes, stdlib HTML escaping only.

Complements groundwork/filemap.py: filemap renders *repo-tree* crumbs
for a concept's file path (``a/b.py`` split on ``/`` with `` / `` joins
and ``#`` hrefs); this module renders *page* crumbs for where the reader
sits in the site (ledger page › module › lesson › card), joined with
``›`` and real page paths. The two never share markup: filemap keeps an
unlabelled ``<nav class='crumbs'>`` inside ``id='filemap'``; this module
owns ``id='crumbs'`` plus ``aria-label``/``aria-current`` and no mini-tree.

Depth patterns (head depends on the entry page)::

    trail([("Modules", "/modules"), (summary, None)])             # module page
    trail([("Due", "/due"), (summary, f"/modules/{mid}"),
           (lesson, f"/modules/{mid}#lesson-{slug}"), (card, None)])  # card depth
"""
from __future__ import annotations

import html

SEPARATOR = " › "


def _text(value) -> str:
    """Coerce a label to stripped text; non-strings become ''."""
    if not isinstance(value, str):
        return ""
    return value.strip()


def _href(value) -> str:
    """Keep only same-site page paths; anything else renders as plain text."""
    if not isinstance(value, str):
        return ""
    v = value.strip()
    if (v.startswith("/") and not v.startswith("//")
            and "\\" not in v
            and not any(ch.isspace() or ch in "\"'<>`" for ch in v)):
        return v
    return ""


def trail(items) -> str:
    """Breadcrumb trail HTML; stable ``id='crumbs'`` anchor.

    ``items`` is a sequence of ``(label, href)`` pairs, shallowest first.
    A falsy/unsafe ``href`` marks that segment as the current page and it
    renders as text with ``aria-current='page'``. Segments with empty
    labels are skipped. Returns ``""`` when nothing renderable remains.
    """
    segs = []
    for item in items or []:
        try:
            label, href = item
        except (TypeError, ValueError):
            continue
        label = _text(label)
        if not label:
            continue
        segs.append((label, _href(href)))
    if not segs:
        return ""
    parts = []
    for i, (label, href) in enumerate(segs):
        last = i == len(segs) - 1
        safe_label = html.escape(label)
        if href and not last:
            parts.append(
                f"<a href='{html.escape(href, quote=True)}'>{safe_label}</a>")
        elif last:
            parts.append(f"<span aria-current='page'>{safe_label}</span>")
        else:
            parts.append(f"<span>{safe_label}</span>")
    return ("<nav class='crumbs' id='crumbs' aria-label='Breadcrumb'>"
            + SEPARATOR.join(parts) + "</nav>")


def section_html() -> str:
    """Status-page subsection with a stable tour anchor (no DB needed)."""
    demo = trail([("Modules", "/modules"), ("Example module", None)])
    return ("<h2 id='status-b6-crumbs'>Page breadcrumbs</h2>"
            "<p>Every nested page opens with its trail — ledger page "
            "(Due, Modules, History) first, then module, lesson, card. "
            "Repo-tree position stays with the file-map mini-view; "
            "this trail answers “where in the site am I?”.</p>"
            f"{demo}")
