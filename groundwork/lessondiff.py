"""Line-by-line lesson version diff (I-116): what changed in the code.

Renders a lesson's ``before``/``after`` code pair as a capped HTML
table of removed/inserted rows with old/new line numbers, plus
added/removed counts. Lessons without the pair render as the empty
string, so ``lessons.render_levels`` stays byte-identical on the
legacy path. Stdlib only (``difflib``, ``html``); never raises.
"""
from __future__ import annotations

import difflib
import html

STATUS_ANCHOR = "status-b20-lessondiff"

MAX_DIFF_ROWS = 60


def normalize_source(value) -> str:
    """Source text for diffing; "" for missing/hostile input."""
    try:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)
    except Exception:  # noqa: BLE001 -- normalizing never raises
        return ""


def pair(lesson) -> tuple:
    """(before, after) strings for a lesson dict; (None, None) when absent.

    ``after`` falls back to the lesson's ``source`` when only ``before``
    is set. Never raises.
    """
    try:
        if not isinstance(lesson, dict):
            return (None, None)
        before = lesson.get("before")
        if before is None:
            return (None, None)
        after = lesson.get("after")
        before = normalize_source(before)
        after = (normalize_source(after) if after is not None
                 else normalize_source(lesson.get("source")))
        if not before and not after:
            return (None, None)
        return (before, after)
    except Exception:  # noqa: BLE001 -- pairing never raises
        return (None, None)


def has_changes(before, after) -> bool:
    """True iff the two sources differ; False on hostile input."""
    try:
        return normalize_source(before) != normalize_source(after)
    except Exception:  # noqa: BLE001
        return False


def diff_ops(before, after) -> list:
    """Row ops for the pair: ("equal"|"del"|"ins", old_no, new_no, text).

    Line numbers are 1-based; the unused side carries None. Empty when
    the sources match. Never raises.
    """
    try:
        a = normalize_source(before).splitlines()
        b = normalize_source(after).splitlines()
        ops = []
        matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    ops.append(("equal", i1 + k + 1, j1 + k + 1, a[i1 + k]))
            elif tag == "delete":
                for k in range(i1, i2):
                    ops.append(("del", k + 1, None, a[k]))
            elif tag == "insert":
                for k in range(j1, j2):
                    ops.append(("ins", None, k + 1, b[k]))
            else:  # replace: removals then additions, in order.
                for k in range(i1, i2):
                    ops.append(("del", k + 1, None, a[k]))
                for k in range(j1, j2):
                    ops.append(("ins", None, k + 1, b[k]))
        return ops
    except Exception:  # noqa: BLE001
        return []


def summary_counts(ops) -> dict:
    """{'added', 'removed'} row counts over diff ops; never raises."""
    try:
        added = sum(1 for op in ops or [] if op[0] == "ins")
        removed = sum(1 for op in ops or [] if op[0] == "del")
        return {"added": added, "removed": removed}
    except Exception:  # noqa: BLE001
        return {"added": 0, "removed": 0}


def _cell(num) -> str:
    return "" if num is None else str(num)


def diff_html(before, after, cap: int = MAX_DIFF_ROWS) -> str:
    """Capped diff table; "" when sources match or input is hostile."""
    try:
        try:
            n = int(cap)
        except (TypeError, ValueError):
            n = MAX_DIFF_ROWS
        ops = diff_ops(before, after)
        rows = [op for op in ops if op[0] != "equal"][:max(0, n)]
        if not rows:
            return ""
        counts = summary_counts(ops)
        body = "".join(
            f"<tr class='lessondiff-{op[0]}'><td>{_cell(op[1])}</td>"
            f"<td>{_cell(op[2])}</td><td>{html.escape(op[3])}</td></tr>"
            for op in rows)
        return (
            f"<table class='lessondiff'><caption>Changed lines "
            f"(+{counts['added']} −{counts['removed']})</caption>"
            f"<tr><th>old</th><th>new</th><th>code</th></tr>{body}</table>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def lesson_block(lesson: dict) -> str:
    """Per-lesson diff view for render_levels; "" with no pair/changes."""
    try:
        before, after = pair(lesson)
        if before is None:
            return ""
        return diff_html(before, after)
    except Exception:  # noqa: BLE001
        return ""


def diff_css() -> str:
    """Raw declarations only (no <style> tags); palette tokens."""
    return (".lessondiff{border-collapse:collapse;font-size:smaller;}"
            ".lessondiff-del{color:var(--ink);background:var(--paper);}"
            ".lessondiff-ins{color:var(--ink);background:var(--paper);}")


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    sample = diff_html("def add(a, b):\n    return a - b\n",
                       "def add(a, b):\n    return a + b\n")
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Lesson version diff <small>(improvement)</small></h3>"
        "<p>When a lesson carries a before/after code pair, the lesson "
        "rendering path (<code>lessons.render_levels</code>) shows what "
        "changed line by line — removed and added rows with old/new "
        "line numbers. <code>groundwork/lessondiff.py</code> renders "
        "nothing when the pair is absent or identical. A live sample "
        "renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "lesson-version-diff",
        "kind": "improvement",
        "title": "Lesson version diff",
        "blurb": "Old versus new code, line by line.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
