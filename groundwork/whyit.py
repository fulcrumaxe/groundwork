"""Per-lesson 'why this matters' from the agent's concept note (I-109).

Lessons open with the agent's one-line reason when the module was filed
with one -- verbatim, escaped, never invented. Lessons without a note
render nothing (byte-identical legacy path). Stdlib only (`html`);
never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b19-whyit"

MAX_NOTE = 500


def clean_note(note) -> str:
    """Usable note text: stripped str, capped; anything else -> ""."""
    try:
        if not isinstance(note, str):
            return ""
        return note.strip()[:MAX_NOTE]
    except Exception:  # noqa: BLE001 -- cleaning never raises
        return ""


def note_for_lesson(lesson: dict, notes) -> str:
    """Lesson's note from a concept_notes mapping; missing -> "".

    Keys tried in order: concept_id, then name (mirrors the pipeline's
    note lookup). Never raises.
    """
    try:
        if not isinstance(lesson, dict) or not isinstance(notes, dict):
            return ""
        for key in (lesson.get("concept_id"), lesson.get("name")):
            if key is not None and key in notes:
                got = clean_note(notes[key])
                if got:
                    return got
        return ""
    except Exception:  # noqa: BLE001
        return ""


def why_for_lesson(lesson: dict, note: str = "") -> str:
    """Lesson-level reason text: explicit note, else stored why_note.

    No templating, no purpose fallback (the Mission header says it
    once), no invention. Never raises.
    """
    try:
        got = clean_note(note)
        if got:
            return got
        if not isinstance(lesson, dict):
            return ""
        return clean_note(lesson.get("why_note"))
    except Exception:  # noqa: BLE001
        return ""


def lesson_why_html(lesson: dict, note: str = "", first: bool = False) -> str:
    """Per-lesson 'Why this matters' aside; empty note -> "".

    The first-section instance carries id='whyit' (tour target);
    later instances render class-only. Never raises.
    """
    try:
        text = why_for_lesson(lesson, note)
        if not text:
            return ""
        tag = " id='whyit'" if first else ""
        return (
            f"<aside class='lesson-why'{tag}><p><small><b>Why this "
            f"matters:</b> {html.escape(text)}</small></p></aside>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch19 home module."""
    sample = lesson_why_html({"name": "add", "why_note": "Checkout totals flow through add."})
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Per-lesson why <small>(improvement)</small></h3>"
        "<p>Lessons open with the agent's one-line concept note when the "
        "module was filed with one — verbatim, escaped, no invention; "
        "lessons without a note render exactly as before. "
        "<code>groundwork/whyit.py</code> provides "
        "<code>why_for_lesson()</code>/<code>lesson_why_html()</code>; the "
        "module page calls it once per lesson section. A live sample renders "
        "below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "lesson-why",
        "kind": "improvement",
        "title": "Why this lesson matters",
        "blurb": "Each lesson opens with the agent's own one-line reason — "
                 "why this concept earns your study time.",
        "path": "/modules/{mid}",
        "anchor": "{lesson}",
    }
