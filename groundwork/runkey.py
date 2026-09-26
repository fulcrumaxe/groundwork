"""Visible Run button with Ctrl+Enter hint on all code exercises (I-155).

The page already submits any textarea form on Ctrl/Cmd+Enter
(web GLOBAL_JS), but nothing says so: code widgets show a bare
"Run tests" button with no shortcut label. This module renders one
labeled Run control plus a form-scoped key handler, so every code
exercise announces and honors the shortcut where it is used.
Choice-button and text-answer cards are untouched.

Pure functions of the exercise-type string — no I/O, no DB changes.
The caller is the code branch of ``cards.answer_widget``.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b24-runkey"

# Mirrors the code-widget branch in cards.answer_widget: every type
# rendered as <textarea name='answer'> + a Run tests submit.
CODE_TYPES = ("12", "14", "19", "20", "23")

DEFAULT_LABEL = "Run tests"


def is_code_exercise(etype) -> bool:
    """True when etype is a code widget; False for anything else."""
    try:
        return str(etype) in CODE_TYPES
    except Exception:  # noqa: BLE001 -- predicate never raises
        return False


def run_button_html(label: str = DEFAULT_LABEL) -> str:
    """Labeled Run submit with a visible Ctrl+Enter hint."""
    try:
        text = label if isinstance(label, str) and label.strip() else DEFAULT_LABEL
    except Exception:  # noqa: BLE001
        text = DEFAULT_LABEL
    return (
        f"<button type='submit' data-runkey>{html.escape(text)} "
        "<kbd>Ctrl+Enter</kbd></button>")


def hint_html() -> str:
    """One-line shortcut hint under the code textarea."""
    return ("<small class='runkey-hint'>Press "
            "<kbd>Ctrl+Enter</kbd> (or Cmd+Enter) to run.</small>")


def exercise_script_js() -> str:
    """Form-scoped Ctrl+Enter handler; clicks this form's Run button.

    Scoped to forms holding a [data-runkey] button, so choice-button
    and text-answer forms keep their exact behavior. Guarded so N
    code cards on one page install exactly one listener (otherwise
    each keypress would click the button N times). Never raises;
    no-ops when the DOM is absent.
    """
    return """
<script>
(function () {
  if (window.__runkeyInit) return;
  window.__runkeyInit = true;
  document.addEventListener('keydown', function (e) {
    if (!(e.ctrlKey || e.metaKey) || e.key !== 'Enter') return;
    var t = e.target;
    if (!t || !t.closest) return;
    var f = t.closest('form');
    if (!f) return;
    var btn = f.querySelector('button[data-runkey]');
    if (!btn) return;
    var tag = (t.tagName || '').toLowerCase();
    if (tag !== 'textarea' && !(tag === 'input' && t.type === 'text')) return;
    e.preventDefault();
    btn.click();
  });
})();
</script>"""


def runkey_for(etype, label: str = DEFAULT_LABEL) -> str:
    """Full Run affordance for one exercise type; "" when not a code widget.

    The "" fallback keeps every non-code card byte-identical (legacy).
    """
    if not is_code_exercise(etype):
        return ""
    return run_button_html(label) + hint_html() + exercise_script_js()


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch24.py."""
    demo = runkey_for("12")
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Run button with shortcut <small>(improvement)</small></h3>"
        "<p>Every code exercise grows a visible Run button labeled with "
        "its <kbd>Ctrl+Enter</kbd> shortcut, plus a form-scoped handler "
        "that clicks exactly that exercise's button. "
        "<code>groundwork/runkey.py</code> plugs into the code branch of "
        "<code>cards.answer_widget</code> (Due queue and module pages); "
        "non-code cards render exactly as before. A live sample renders "
        "below.</p>"
        f"<p><form method='post' action='/cards/demo/review'>"
        f"<textarea name='answer' rows='3' cols='60'></textarea><br>{demo}</form></p>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "run-key",
        "kind": "improvement",
        "title": "Run button with shortcut",
        "blurb": "Every code exercise shows a Run button with its "
                 "Ctrl+Enter shortcut — run from the keyboard, no mouse needed.",
        "path": "/due",
        "anchor": "up-next",
    }
