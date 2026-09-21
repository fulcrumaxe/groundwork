"""Concept-chip lesson links: every concept chip jumps to its lesson (I-22).

Module pages already tag each lesson `<section id='lesson-<slug>'>`
(see lessons.slug and web.module_html); the status chip beside each
lesson title was plain text. These helpers link it to
`/modules/<mid>#lesson-<slug>` so the chip is a deep link home.

Pure helpers over ids — no I/O, no DB or schema changes, stdlib only.
The slug is mirrored locally from lessons.slug (no groundwork imports)
so the module stays import-safe standalone, exactly like
cardlinks.py / copylink.py.
"""
from __future__ import annotations

import html


def slug(text) -> str:
    """Fragment-safe slug for a concept name; "lesson" when blank.

    Mirrors lessons.slug exactly (lowercases; non-alnum become dashes;
    runs collapse) so chip hrefs always match the section anchors.
    """
    if not isinstance(text, str):
        return "lesson"
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    out = "-".join(p for p in out.split("-") if p)
    return out or "lesson"


def lesson_anchor(concept) -> str:
    """Anchor id of a concept's lesson section: lesson-<slug>."""
    return f"lesson-{slug(concept)}"


def chip_href(module_id, concept) -> str:
    """Deep link to a concept's lesson section.

    Returns "" when the module id is blank, and the bare module URL
    when the concept is blank — mirroring cardlinks.card_url.
    """
    mid = html.escape(module_id, quote=True) if isinstance(module_id, str) else ""
    if not mid:
        return ""
    if not isinstance(concept, str) or not concept.strip():
        return f"/modules/{mid}"
    anchor = html.escape(lesson_anchor(concept), quote=True)
    return f"/modules/{mid}#{anchor}"


def chip_link(module_id, concept, label=None, extra: str = "") -> str:
    """Status-chip HTML wrapped in its lesson link.

    Label falls back to the concept name; renders a plain (unlinked)
    chip when the href is unbuildable. Never raises.
    """
    if isinstance(label, str) and label:
        text = label
    elif isinstance(concept, str) and concept:
        text = concept
    else:
        text = ""
    tail = extra if isinstance(extra, str) else ""
    try:
        from . import ownedbadge as ownedbadgemod
        cls = ownedbadgemod.badge_class(text)
    except Exception:  # noqa: BLE001 — chips must never break links
        cls = "chip"
    body = f"<span class='{cls}'{tail}>{html.escape(text)}</span>"
    url = chip_href(module_id, concept)
    if not url:
        return body
    return f"<a href='{url}'>{body}</a>"


def section_html(db_path: str = "") -> str:
    """Status subsection with a stable tour anchor (I-22).

    Takes an optional db_path purely for drop-in status.py wiring —
    the copy needs no database, so the argument is accepted and unused.
    """
    del db_path
    return (
        "<h2 id='status-b7-chiplinks'>Concept-chip lesson links</h2>"
        "<p>Every concept's status chip on its module page links to "
        "<code>/modules/&lt;mid&gt;#lesson-&lt;slug&gt;</code> — the "
        "lesson section it already sits in — so chips are deep links, "
        "not plain text.</p>"
    )
