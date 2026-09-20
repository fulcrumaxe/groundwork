"""Card deep-links: History entries jump to the exact card (I-7).

Lesson sections already deep-link as `#lesson-<slug>` (see copylink.py
and lessons.slug). Cards get the parallel convention `#card-<cid>`:
the module page tags each card's `<article>` with the anchor, and each
History attempt entry links to `/modules/<mid>#card-<cid>`.

Pure helpers over ids — no I/O, no DB or schema changes, stdlib only.
Case is preserved (card ids are keys; lowercasing could collide two
ids), otherwise sanitised exactly like copylink slugs so the anchor is
always fragment-safe and never collides with `lesson-*`.
"""
from __future__ import annotations

import html


def _safe(token) -> str:
    """Fragment-safe token: alnum plus - and _, rest become dashes."""
    if not isinstance(token, str):
        return ""
    out = "".join(ch if (ch.isalnum() or ch in "-_") else "-" for ch in token)
    return "-".join(p for p in out.split("-") if p)


def card_anchor(cid) -> str:
    """Anchor id for one card's `<article>`; "" when the id is blank."""
    safe = _safe(cid)
    if not safe:
        return ""
    return f"card-{safe}"


def card_url(module_id, cid) -> str:
    """Deep link to the exact card; bare module URL when ids are blank."""
    anchor = card_anchor(cid)
    mid = html.escape(module_id, quote=True) if isinstance(module_id, str) else ""
    if not mid:
        return ""
    if not anchor:
        return f"/modules/{mid}"
    return f"/modules/{mid}#{html.escape(anchor, quote=True)}"


def article_open(cid) -> str:
    """Opening `<article>` tag for a card, carrying its deep-link anchor."""
    anchor = card_anchor(cid)
    if not anchor:
        return "<article>"
    return f"<article id='{html.escape(anchor, quote=True)}'>"


def history_link(module_id, cid, label) -> str:
    """Attempt-entry link to the exact card; label falls back to module id."""
    text = label if isinstance(label, str) and label else (
        module_id if isinstance(module_id, str) else "")
    url = card_url(module_id, cid)
    if not url:
        return html.escape(text)
    return f"<a href='{url}'>{html.escape(text)}</a>"


def copy_anchor(anchor) -> str:
    """Per-card `#` copy-link, mirroring copylink.copy_link's shape."""
    slug = card_anchor(anchor)
    if not slug:
        return ""
    safe = html.escape(slug, quote=True)
    return (
        f"<a class='copylink' href='#{safe}' "
        f"data-copy-anchor='#{safe}' title='Copy link'>#</a>"
    )


def section_html(db_path: str = "") -> str:
    """Status subsection with a stable tour anchor (I-7).

    Takes an optional db_path purely for drop-in status.py wiring —
    the copy needs no database, so the argument is accepted and unused.
    """
    del db_path
    return (
        "<h2 id='status-b6-cardlinks'>Card deep-links</h2>"
        "<p>Every card carries a <code>#card-&lt;id&gt;</code> anchor on "
        "its module page, next to the <code>#lesson-&lt;slug&gt;</code> "
        "lesson anchors — and every History attempt links straight to "
        "the exact card it graded.</p>"
    )
