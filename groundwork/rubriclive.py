"""Live rubric checklist beside explain textareas (I-167).

Server renders the card's rubric keywords as an unchecked list next to
explain textareas; a small client script ticks items as the learner
types matching keywords (case-insensitive, word-boundary). Advisory
only — grading untouched. Pure functions, stdlib only, no I/O.
"""
from __future__ import annotations

import html
import json
import re

STATUS_ANCHOR = "status-b25-rubriclive"

# Rubric-graded explain family: payload["rubric"] is the grader's own
# keyword list (exercises.grade 5/6/25 + 21/24 half-bars; 83/85/86
# rubberduck/feynman/analogy plugin graders). Type 22 excluded: its
# grade is first-letter choice, so a keyword list would mislead.
EXPLAIN_TYPES = ("5", "6", "21", "24", "25", "83", "85", "86")


def _field(card, name, default=""):
    """card[name] for dicts and sqlite Rows; default when missing."""
    try:
        return card[name]
    except (KeyError, IndexError, TypeError):
        try:
            return card.get(name, default)
        except AttributeError:
            return default


def rubric_for(card) -> list:
    """Rubric keywords for a card; [] when absent/unparseable."""
    try:
        p = _field(card, "payload", {})
        if isinstance(p, str):
            try:
                p = json.loads(p or "{}")
            except ValueError:
                return []
        if not isinstance(p, dict):
            return []
        return [str(w) for w in (p.get("rubric", []) or []) if w]
    except Exception:  # noqa: BLE001 -- checklist never breaks cards
        return []


def _hit(text: str, kw: str) -> bool:
    if not kw:
        return False
    try:
        if re.search(r"\w", kw):
            return re.search(r"\b" + re.escape(kw) + r"\b",
                             text, re.IGNORECASE) is not None
    except re.error:
        pass
    return kw.lower() in text.lower()


def matched(text, rubric) -> list:
    """Per-keyword hit flags (server mirror of client ticking)."""
    t = text if isinstance(text, str) else str(text or "")
    return [_hit(t, str(k)) for k in (rubric or [])]


def checklist_html(card_id, rubric) -> str:
    """Unchecked rubric list; "" when no rubric (legacy fallback)."""
    items = [str(w) for w in (rubric or []) if w]
    if not items:
        return ""
    lis = "".join(
        f"<li data-kw='{html.escape(w, quote=True)}'>"
        f"<span aria-hidden='true'>[ ]</span> {html.escape(w)}</li>"
        for w in items)
    return (
        f"<aside class='rubriclive' id='rl-{html.escape(str(card_id))}'>"
        f"<small>Key points (advisory — grading unchanged)</small>"
        f"<ul>{lis}</ul></aside>")


def script_js() -> str:
    """One guarded listener: tick items on textarea input."""
    return """
<script>
if (!window.__rubricliveInit) { window.__rubricliveInit = true;
document.addEventListener('input', function (e) {
  var box = e.target.closest ? e.target.closest('textarea[name=answer]') : null;
  if (!box) return;
  var side = box.parentElement.querySelector('.rubriclive');
  if (!side) return;
  var text = box.value || '';
  Array.prototype.forEach.call(side.querySelectorAll('li[data-kw]'), function (li) {
    var kw = li.getAttribute('data-kw') || '';
    var hit = false;
    try {
      hit = new RegExp('\\\\b' + kw.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + '\\\\b', 'i').test(text);
    } catch (err) { hit = text.toLowerCase().indexOf(kw.toLowerCase()) >= 0; }
    li.querySelector('span').textContent = hit ? '[x]' : '[ ]';
  });
});
}
</script>"""


def enhance(card, textarea_html: str) -> str:
    """Textarea + live checklist; legacy bytes when no rubric data."""
    try:
        etype = str(_field(card, "exercise_type", ""))
    except (AttributeError, TypeError):
        return textarea_html
    if etype not in EXPLAIN_TYPES:
        return textarea_html
    cid = _field(card, "id", "")
    side = checklist_html(cid, rubric_for(card))
    if not side:
        return textarea_html
    return (f"<div class='rubriclive-wrap'>{textarea_html}{side}</div>"
            + script_js())


def tour_entry() -> dict:
    """Tour registry entry for the live rubric checklist."""
    return {"id": "live-rubric-checklist", "kind": "improvement",
            "title": "Live rubric checklist",
            "blurb": ("Explain answers tick their rubric keywords live as "
                      "you type — advisory, never graded."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch25.py."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Live rubric checklist "
        "<small>(improvement)</small></h3>"
        "<p>Explain textareas show their rubric keywords beside the box, "
        "ticking as you type — advisory only, grading untouched. "
        "<code>groundwork/rubriclive.py</code>.</p>")
