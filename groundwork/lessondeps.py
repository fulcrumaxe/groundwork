"""Lesson dependencies (I-131): "understand X first" jump links per lesson.

Each lesson may declare what it builds on (``needs`` / ``depends_on``);
``deps_for`` resolves those names against earlier lessons and ``deps_html``
renders the understand-first list with jump links. Pure HTML builders over
lesson dicts -- no I/O, no DB changes. Anchors reuse ``lessons.slug`` with
the ``lesson-`` prefix so jump links match the lesson section ids emitted
by ``Handler.module_html`` (``<section id='lesson-<slug>'>``). Lessons
without dependency data render ``""`` so pages keep legacy bytes.

Caller path (real learner/reader, never a Status demo): the per-concept
loop in ``Handler.module_html`` appends ``deps_html(lesson_map[node],
earlier)`` beside the render_levels/beforafter blocks, where ``earlier``
is the lesson dicts of the sections rendered above. No other web.py
logic; no DB/schema changes.
"""
from __future__ import annotations

import html

from .lessons import slug as lesson_slug

STATUS_ANCHOR = "status-b21-lessondeps"

_NEED_KEYS = ("needs", "depends_on")


def _name_of(item) -> str:
    """Display name of a lesson dict, concept row, or plain string."""
    try:
        if isinstance(item, dict):
            for key in ("name", "concept"):
                value = item.get(key, "")
                if isinstance(value, str) and value.strip():
                    return value
            return ""
        return str(item) if item is not None else ""
    except Exception:  # noqa: BLE001 -- naming never raises
        return ""


def needs_of(lesson) -> list:
    """Declared dependency names of one lesson dict; [] when none/hostile."""
    try:
        if not isinstance(lesson, dict):
            return []
        out = []
        for key in _NEED_KEYS:
            raw = lesson.get(key, [])
            if isinstance(raw, str):
                raw = [raw]
            if not isinstance(raw, (list, tuple)):
                continue
            for need in raw:
                if isinstance(need, str) and need.strip() \
                        and need.strip() not in out:
                    out.append(need.strip())
        return out
    except Exception:  # noqa: BLE001 -- lookup never raises
        return []


def deps_for(lesson, earlier) -> list:
    """Needs of ``lesson`` matched against ``earlier`` lessons.

    Emitted in earlier-teaching order (the order a reader meets them).
    Matching is slug-based so ``"For Loops"`` finds ``"for loops"``.
    Unmatched needs (nothing taught yet) are dropped so no dead link
    ever renders, as is a need naming the lesson itself exactly.
    Never raises; hostile input yields [].
    """
    try:
        if not isinstance(lesson, dict):
            return []
        order: list = []
        seen: set = set()
        for item in (earlier or []):
            name = _name_of(item).strip()
            key = lesson_slug(name) if name else ""
            if key and key not in seen:
                seen.add(key)
                order.append(name)
        index = {lesson_slug(n): n for n in order}
        own = _name_of(lesson)
        wanted: set = set()
        for need in needs_of(lesson):
            if need == own:
                continue  # names itself: never a dead self jump
            key = lesson_slug(need)
            if key and key in index:
                wanted.add(key)
        return [n for n in order if lesson_slug(n) in wanted]
    except Exception:  # noqa: BLE001 -- resolution never raises
        return []


def deps_html(lesson, earlier) -> str:
    """Understand-first list with jump links; "" with no dependencies."""
    try:
        deps = deps_for(lesson, earlier)
        if not deps:
            return ""
        links = []
        for name in deps:
            anchor = "lesson-" + lesson_slug(name)
            links.append(
                f"<a href='#{html.escape(anchor, quote=True)}'>"
                f"{html.escape(name)}</a>")
        return ("<p class='deps'><small>Understand first: "
                + " · ".join(links) + "</small></p>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch21 home module."""
    try:
        sample = deps_html({"name": "c", "needs": ["a", "b"]},
                           [{"name": "a"}, {"name": "b"}])
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Lesson dependencies "
            "<small>(improvement)</small></h3>"
            "<p>Each lesson lists what to understand first, with jump "
            "links back to the earlier lesson sections. "
            "<code>groundwork/lessondeps.py</code> resolves a lesson's "
            "<code>needs</code> against earlier lessons on the lesson "
            "rendering path (<code>Handler.module_html</code>); lessons "
            "without dependency data render exactly as before.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must never raise
        return (f"<h3 id='{STATUS_ANCHOR}'>Lesson dependencies</h3>"
                "<p>Dependency help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "lesson-dependencies",
        "kind": "improvement",
        "title": "Lesson dependencies",
        "blurb": ("Each lesson lists what to understand first, with "
                  "jump links back to the earlier lesson sections."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
