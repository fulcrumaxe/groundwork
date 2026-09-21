"""Line numbers for code blocks, sharing the Batch 1 copy button (I-61).

Every lesson and exercise code block renders as a plain pre element
(lessons.py, plus commitmsg/cssfix/golf/i18n/perffix/rebase renderers;
renameex uses pre > code). Batch 1 already wraps each pre in a
.codewrap div with a .copybtn that copies pre.innerText (web.py
GLOBAL_JS) -- so this module adds line numbers as pure CSS counters on
those same pre/code selectors: no second button, no JavaScript, no
web.py edits.

Counter mechanics: each pre resets a codeline counter; each per-line
element (.codeline, wrapped by numbered_html()) increments it; its
::before paints the value into a gutter. Degradation is structural:
numbers exist ONLY as ::before generated content, so a browser without
counter support renders the same block with an empty gutter --
readable, nothing hidden, nothing broken. Gutter numbers carry
user-select:none so manual selection skips them and copies stay clean;
the .copybtn corner is untouched. Wrapping lines in spans leaves
pre.innerText unchanged, so the Batch 1 copy script keeps working.
Pure functions, stdlib only, no I/O; every helper fails closed and
never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b10-codelines"

_COUNTER = "codeline"


def _safe_text(value) -> str:
    """Best-effort str(); empty string for anything unusable, never raises."""
    try:
        if isinstance(value, str):
            return value
        if value is None:
            return ""
        return str(value)
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return ""


def line_count(text) -> int:
    """Number of lines in a code string; 0 for empty/non-string, never raises."""
    try:
        body = _safe_text(text)
        if not body:
            return 0
        return body.count("\n") + 1
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return 0


def numbered_html(code) -> str:
    """Wrap each line of code in a .codeline span; never raises.

    Takes RAW code (escapes it here) so renderers swap one call for
    their html.escape: ``numbered_html(raw)``. Spans preserve the exact
    text (innerText unchanged), so the Batch 1 copy button copies the
    same characters. Unusable input fails closed to "".
    """
    try:
        body = _safe_text(code)
        if not body:
            return ""
        lines = body.split("\n")
        return "\n".join(
            f"<span class='codeline'>{html.escape(l)}</span>"
            for l in lines)
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return ""


def codelines_css() -> str:
    """Raw CSS declarations numbering code lines via counters.

    Concatenated into the head wire by the parent (as stack_css() is);
    NEVER style tags, only declarations. Targets the pre/code
    selectors the Batch 1 copy script already wraps, so numbers and
    the existing Copy button share each block.
    """
    try:
        return "".join([
            f"pre{{counter-reset:{_COUNTER}}}",
            f"pre code{{counter-reset:{_COUNTER}}}",
            f"code .codeline,pre .codeline{{display:block;"
            f"counter-increment:{_COUNTER};line-height:1.5}}",
            f"code .codeline::before,pre .codeline::before{{"
            f"content:counter({_COUNTER});display:inline-block;"
            f"width:2.2em;margin-right:.8em;text-align:right;"
            f"color:var(--stale,#888);user-select:none;"
            f"-webkit-user-select:none}}",
        ])
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Code line numbers "
            f"<small>(improvement)</small></h3>"
            "<p>Every <code>pre</code> code block now numbers its lines via "
            "CSS counters from <code>groundwork/codelines.py</code>: each "
            "block resets the counter, each per-line element increments it, "
            "and a selection-proof gutter paints the value -- no JavaScript, "
            "no web.py edits. The Copy button is the pre-existing Batch 1 "
            "one (web.py wraps each block in <code>.codewrap</code> with a "
            "<code>.copybtn</code>); this item wires numbers to those same "
            "blocks instead of shipping a second competing button. "
            "<code>codelines_css()</code> returns raw declarations for the "
            "head wire, <code>numbered_html()</code> wraps escaped lines in "
            "<code>.codeline</code> spans (innerText unchanged, so copies "
            "stay clean), and <code>line_count()</code> counts lines while "
            "failing closed on bad input. Without counter support the same "
            "blocks render plain -- readable, nothing hidden.</p>"
        )
    except Exception:  # noqa: BLE001 -- status page must never break
        return f"<h3 id='{STATUS_ANCHOR}'>Code line numbers</h3>"
