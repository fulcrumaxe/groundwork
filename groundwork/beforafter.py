"""Before/after diff view per lesson (I-107): what the agent changed.

Renders the lesson's `before`/`after` code pair as a capped unified diff
plus added/removed line counts. Lessons without the pair render as the
empty string, so the parent page stays byte-identical to the legacy path.
Stdlib only (`difflib`, `html`); never raises.
"""
from __future__ import annotations

import difflib
import html

STATUS_ANCHOR = "status-b19-beforafter"

MAX_DIFF_LINES = 60


def pair(lesson) -> tuple:
    """(before, after) strings for a lesson dict; (None, None) when absent.

    `after` falls back to the lesson's `source` when only `before` is
    set. Never raises.
    """
    try:
        if not isinstance(lesson, dict):
            return (None, None)
        before = lesson.get("before")
        after = lesson.get("after")
        if before is None and after is None:
            return (None, None)
        if before is None:
            return (None, None)
        before = str(before)
        after = str(after) if after is not None else str(lesson.get("source") or "")
        if not before and not after:
            return (None, None)
        return (before, after)
    except Exception:  # noqa: BLE001 -- pairing never raises
        return (None, None)


def diff_stats(before: str, after: str) -> dict:
    """{'added', 'removed'} line counts over the pair; never raises."""
    try:
        a = str(before or "").splitlines()
        b = str(after or "").splitlines()
        # Count from the unified diff itself: one pass, no double counting.
        added, removed = 0, 0
        for line in difflib.unified_diff(a, b, lineterm=""):
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+"):
                added += 1
            elif line.startswith("-"):
                removed += 1
        return {"added": added, "removed": removed}
    except Exception:  # noqa: BLE001
        return {"added": 0, "removed": 0}


def unified_diff(before: str, after: str, cap: int = MAX_DIFF_LINES) -> str:
    """Capped unified diff text ('--- before' / '+++ after'); never raises."""
    try:
        try:
            n = int(cap)
        except (TypeError, ValueError):
            n = MAX_DIFF_LINES
        lines = list(difflib.unified_diff(
            str(before or "").splitlines(),
            str(after or "").splitlines(),
            fromfile="before", tofile="after", lineterm=""))
        return "\n".join(lines[:max(0, n)])
    except Exception:  # noqa: BLE001
        return ""


def lesson_block(lesson: dict, anchor: bool = False) -> str:
    """Per-lesson diff view; '' when the lesson carries no pair."""
    try:
        before, after = pair(lesson)
        if before is None and after is None:
            return ""
        stats = diff_stats(before, after)
        diff = unified_diff(before, after)
        tag = " id='beforafter'" if anchor else ""
        return (
            f"<div{tag}><p><small>{stats['added']} added, "
            f"{stats['removed']} removed by the agent in this lesson.</small></p>"
            f"<details><summary>Show what changed</summary>"
            f"<pre>{html.escape(diff)}</pre></details></div>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch19 home module."""
    sample = lesson_block({"before": "x = 1\n", "after": "x = 2\n"})
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Before/after diff <small>(improvement)</small></h3>"
        "<p>Each lesson shows what the agent changed: added/removed counts "
        "with the capped diff one click away. "
        "<code>groundwork/beforafter.py</code> reads the lesson's optional "
        "<code>before</code>/<code>after</code> keys on the module reading "
        "path (<code>Handler.module_html</code>); lessons without the pair "
        "render exactly as before. A live sample renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "beforafter-diff",
        "kind": "improvement",
        "title": "Before/after diff per lesson",
        "blurb": "Each lesson shows what the agent changed: added/removed "
                 "counts with the capped diff one click away.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
