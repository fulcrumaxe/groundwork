"""Collapse long lesson source blocks (I-108).

Length-gated renderer: short code returns today's plain <pre> block
byte-identical; long code returns a visible head plus a closed native
<details> expander holding the complete numbered block. Owns ONLY
length-based collapsing of lesson source blocks -- predict.py owns
predict-then-reveal covers, codelines.py owns gutters/copy text,
collapse.py owns answered-card collapse. No ids, no scripts, no
styles; stdlib only (`html`); never raises.
"""
from __future__ import annotations

import html

from . import codelines as codemod

STATUS_ANCHOR = "status-b19-srccollapse"

MAX_VISIBLE_LINES = 12
HEAD_LINES = 8
SUMMARY_TEXT = "Show full file context"


def line_count(source) -> int:
    """Lines in a code string; 0 for empty/hostile input, never raises."""
    try:
        return codemod.line_count(source)
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return 0


def is_long(source, max_lines: int = MAX_VISIBLE_LINES) -> bool:
    """True iff the source exceeds the visible threshold."""
    try:
        try:
            limit = int(max_lines)
        except (TypeError, ValueError):
            limit = MAX_VISIBLE_LINES
        if limit <= 0:
            limit = MAX_VISIBLE_LINES
        return line_count(source) > limit
    except Exception:  # noqa: BLE001
        return False


def head_lines(source, n: int = HEAD_LINES) -> str:
    """First n raw lines; "" for empty/hostile input, never raises."""
    try:
        if not isinstance(source, str) or not source:
            return ""
        try:
            count = int(n)
        except (TypeError, ValueError):
            count = HEAD_LINES
        if count <= 0:
            return ""
        return "\n".join(source.splitlines()[:count])
    except Exception:  # noqa: BLE001
        return ""


def block_html(code=None, *, max_lines: int = MAX_VISIBLE_LINES,
               context_lines: int = HEAD_LINES) -> str:
    """Raw code -> <pre> block, collapsing long blocks behind an expander.

    Short input returns exactly today's markup byte-identical; long
    input returns a head <pre> plus a closed <details> expander with
    the full block. Empty input returns "". Never raises.
    """
    try:
        if code is None:
            return ""
        if not isinstance(code, str):
            try:
                code = str(code)
            except Exception:  # noqa: BLE001
                return ""
        if not code:
            return ""
        if not is_long(code, max_lines):
            return f"<pre>{codemod.numbered_html(code)}</pre>"
        total = line_count(code)
        head = codemod.numbered_html(head_lines(code, context_lines))
        full = codemod.numbered_html(code)
        return (
            f"<div class='srcblock'><pre>{head}</pre>"
            f"<details class='srccollapse'><summary>{SUMMARY_TEXT} "
            f"({total} lines)</summary><pre>{full}</pre></details></div>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch19 home module."""
    demo = "\n".join(f"def f{i}():\n    return {i}" for i in range(10))
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Long source blocks collapse <small>(improvement)</small></h3>"
        "<p>Long lesson source hides behind a Show full file context "
        "expander — short snippets read on. "
        "<code>groundwork/srccollapse.py</code> gates on line count at the "
        "two source-emission sites in <code>lessons.render_levels</code>; "
        "the full text stays in the DOM, readable with JavaScript disabled. "
        "A live sample renders below.</p>"
        f"{block_html(demo)}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "src-context",
        "kind": "improvement",
        "title": "Collapsible source blocks",
        "blurb": "Long lesson source hides behind a Show full file context "
                 "expander — short snippets read on.",
        "path": "/modules/{mid}",
        "anchor": "{lesson}",
    }
