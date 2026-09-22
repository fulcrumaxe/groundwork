"""Worked-example replay (I-105): step through the measured trace one
step at a time.

Pure-HTML slicing over the already-stored ``worked.trace.steps`` /
``dualcode.states``: one step row plus prev/next links and a counter.
Empty trace renders "" so the caller keeps its legacy full pack.
Stdlib only (`html`); never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b19-replay"
MAX_STEPS = 8


def replay_steps(lesson) -> list:
    """One {step, does, state} row per measured trace step; [] when absent.

    Only the sandbox-measured ``worked.trace.steps`` qualifies: diagram
    steps without a trace keep their legacy full pack (Batch 16).
    """
    try:
        if not isinstance(lesson, dict):
            return []
        worked = lesson.get("worked") or {}
        trace = worked.get("trace") or {} if isinstance(worked, dict) else {}
        steps = trace.get("steps") or [] if isinstance(trace, dict) else []
        if not isinstance(steps, list) or not steps:
            return []
        dc = lesson.get("dualcode") or {}
        states = dc.get("states") or [] if isinstance(dc, dict) else []
        if not isinstance(states, list):
            states = []
        how = lesson.get("how") or []
        if not isinstance(how, list):
            how = []
        rows = []
        for i, st in enumerate(steps[:MAX_STEPS]):
            does = str(how[i]) if i < len(how) else ""
            rows.append({"step": i + 1, "does": does, "state": str(st)})
        return rows
    except Exception:  # noqa: BLE001 -- slicing never raises
        return []


def clamp_step(lesson, step) -> int | None:
    """1-based active step clamped to [1, len]; None when no replay."""
    try:
        rows = replay_steps(lesson)
        if not rows:
            return None
        try:
            k = int(str(step).strip())
        except (TypeError, ValueError, AttributeError):
            k = 1
        return max(1, min(k, len(rows)))
    except Exception:  # noqa: BLE001
        return None


def replay_html(lesson, step=1, base_path: str = "") -> str:
    """Stepped trace block, or "" when the lesson has no trace."""
    try:
        rows = replay_steps(lesson)
        if not rows:
            return ""
        k = clamp_step(lesson, step) or 1
        base = str(base_path or "")
        row = rows[k - 1]
        dots = " ".join(
            f"<b>{r['step']}</b>" if r["step"] == k else str(r["step"])
            for r in rows)
        prev_link = (f"<a href='{base}?replay={k - 1}#replay'>← prev</a>"
                     if k > 1 else "<span>← prev</span>")
        next_link = (f"<a href='{base}?replay={k + 1}#replay'>next →</a>"
                     if k < len(rows) else "<span>next →</span>")
        return (
            f"<div class='replay' id='replay'>"
            f"<h5>Worked replay — Step {k} of {len(rows)}</h5>"
            f"<table class='log'><tr><th>Step</th><th>Does</th><th>State</th></tr>"
            f"<tr><td>{k}</td><td>{html.escape(row['does'])}</td>"
            f"<td>{html.escape(row['state'])}</td></tr></table>"
            f"<p><small>{prev_link} · {dots} · {next_link}</small></p>"
            f"</div>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch19 home module."""
    sample = replay_html({"worked": {"call": "add(2, 3)", "output": "5",
                                     "trace": {"var": "total",
                                               "steps": ["1", "3", "5"]}},
                          "how": ["Sets `total`.", "Adds.", "Hands back."],
                          "dualcode": {"steps": [], "states": []}}, 2, "")
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Worked-example replay <small>(improvement)</small></h3>"
        "<p>Long traces now replay one step at a time — prev/next with the "
        "measured state at each step. <code>groundwork/replay.py</code> slices "
        "the already-stored trace on the lesson rendering path "
        "(<code>lessons.render_levels</code>); lessons without a trace keep "
        "the full pack. A live sample renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "worked-replay",
        "kind": "improvement",
        "title": "Worked-example replay",
        "blurb": "Step through the measured trace one step at a time — "
                 "prev/next with the state at each step.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
