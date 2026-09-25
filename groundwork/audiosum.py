"""Lesson audio summaries via offline speech synthesis (I-141).

Each lesson grows a spoken summary (at most 60 words, drawn from the
lesson's own summary plus its first how-step) behind a Listen button
that reads it aloud through the Web Speech API — no network, no
stored audio, nothing to transcribe. Progressive enhancement all the
way down: lessons without study text render byte-identical (the block
is empty), without JS nothing injects, and without speechSynthesis
the script returns early. A second click stops. Pure string
emitters, stdlib only; never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b23-audiosum"

BUTTON_CLASS = "audiosum-listen"
BUTTON_LABEL = "Listen to summary"
MAX_WORDS = 60


def _words(value) -> list:
    if value is None:
        return []
    if isinstance(value, str):
        return value.split()
    if isinstance(value, (list, tuple)):
        out = []
        for v in value:
            out.extend(_words(v))
        return out
    if isinstance(value, dict):
        out = []
        for v in value.values():
            out.extend(_words(v))
        return out
    return str(value).split()


def summary_text(lesson: dict, max_words: int = MAX_WORDS) -> str:
    """Spoken summary: lesson summary plus first how-step, word-capped."""
    try:
        if not isinstance(lesson, dict):
            return ""
        bits = _words(lesson.get("summary"))
        how = lesson.get("how")
        if isinstance(how, (list, tuple)) and how:
            bits.extend(_words(how[0]))
        elif isinstance(how, str):
            bits.extend(how.split())
        try:
            cap = int(max_words)
        except (TypeError, ValueError):
            cap = MAX_WORDS
        if cap <= 0:
            return ""
        return " ".join(bits[:cap])
    except Exception:  # noqa: BLE001 -- summary must never raise
        return ""


def block_html(lesson: dict) -> str:
    """Listen button plus transcript; empty string when no summary."""
    try:
        text = summary_text(lesson)
        if not text:
            return ""
        return (
            f"<div class='audiosum'><button class='{BUTTON_CLASS}' "
            f"type='button'>{BUTTON_LABEL}</button>"
            f"<p class='audiosum-text'>{html.escape(text)}</p></div>")
    except Exception:  # noqa: BLE001 -- lesson render must never break
        return ""


def script_js() -> str:
    """Page wire: Listen buttons speak their transcript, guarded."""
    return (
        "<script data-audiosum>"
        "(function(){try{"
        "if(!('speechSynthesis' in window))return;"
        "function speak(t){try{"
        "if(window.speechSynthesis.speaking){window.speechSynthesis.cancel();return;}"
        "window.speechSynthesis.cancel();"
        "window.speechSynthesis.speak(new SpeechSynthesisUtterance(t));"
        "}catch(e){}}"
        "document.querySelectorAll('.audiosum').forEach(function(box){"
        "var b=box.querySelector('." + BUTTON_CLASS + "');"
        "if(!b||b.dataset.wired)return;"
        "b.dataset.wired='1';"
        "b.addEventListener('click',function(){"
        "var p=box.querySelector('.audiosum-text');"
        "if(!p)return;"
        "speak(p.textContent);});});"
        "}catch(e){}})</script>")


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Audio summaries "
            "<small>(improvement)</small></h3>"
            "<p>Lessons that speak — "
            "<code>groundwork/audiosum.py</code> renders a Listen button "
            "with a spoken summary (the lesson's own words, at most 60) "
            "and one page script reads it via speechSynthesis (click "
            "toggles stop); no summary, no JS, or no speech support "
            "means the page renders exactly as before.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Audio summaries</h3>"
                "<p>Audio summary help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "audio-summaries",
        "kind": "improvement",
        "title": "Audio summaries",
        "blurb": ("Lessons grow a Listen button — the summary, spoken "
                  "offline."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
