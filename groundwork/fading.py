"""Worked-example fading sequences: full -> partial -> solo (F-57).

Library helper over a concept's worked trace steps (the ``steps`` list
inside ``lesson["worked"]["trace"]`` — see ``pipeline.py`` callers and
``modules.py``/``explain.py`` renderers). Fading stages map onto the
``hinttiers`` tier vocabulary — full=worked, partial=pointer,
solo=nudge — by name only: this module never imports groundwork code
and never reimplements tier CSS, it just labels each stage with its
tier so the parent can style them together. LIBRARY only: not a new
graded exercise type, no pipeline/exercises/grading changes, no DB or
schema changes. Pure functions, stdlib only (``html``), no I/O.
"""
from __future__ import annotations

import html as htmlmod

STAGES = ("full", "partial", "solo")

STATUS_ANCHOR = "status-b12-fading"

# Fading stage -> hinttiers tier name (vocabulary reuse, no import).
STAGE_TIER = {
    "full": "worked",
    "partial": "pointer",
    "solo": "nudge",
}

STAGE_TITLE = {
    "full": "Full worked example",
    "partial": "Partial — hide the last step",
    "solo": "Solo — show the first step only",
}


def _steps_of(worked_steps) -> list:
    """Coerced step list; hostile or empty input fails closed to []."""
    try:
        if not isinstance(worked_steps, (list, tuple)):
            return []
        out = []
        for s in worked_steps:
            if s is None:
                continue
            text = s if isinstance(s, str) else str(s)
            if text.strip():
                out.append(text)
        return out
    except Exception:  # noqa: BLE001 — coercion must never raise
        return []


def stage_tier(stage) -> str:
    """Hint-tier name for a fading stage; unknown input -> "nudge"."""
    try:
        if isinstance(stage, str) and stage.strip().lower() in STAGE_TIER:
            return STAGE_TIER[stage.strip().lower()]
    except Exception:  # noqa: BLE001 — lookup must never raise
        pass
    return "nudge"


def fade_sequence(worked_steps: list) -> list:
    """Three fading stages over worked trace steps; never raises.

    Full shows all steps, partial hides the last step, solo shows the
    first step only. Empty (or hostile) input fails closed to [].
    Each item is {"stage", "shown": [...], "hidden": [...]}.
    """
    try:
        steps = _steps_of(worked_steps)
        if not steps:
            return []
        return [
            {"stage": "full", "shown": list(steps), "hidden": []},
            {"stage": "partial",
             "shown": list(steps[:-1]), "hidden": [steps[-1]]},
            {"stage": "solo",
             "shown": [steps[0]], "hidden": list(steps[1:])},
        ]
    except Exception:  # noqa: BLE001 — sequencer must never raise
        return []


def _stage_html(item) -> str:
    """One escaped details/summary disclosure for a sequence item."""
    try:
        if not isinstance(item, dict):
            return ""
        stage = item.get("stage") if isinstance(item.get("stage"), str) else ""
        key = stage.strip().lower() if stage else ""
        if key not in STAGE_TIER:
            return ""
        shown = item.get("shown")
        hidden = item.get("hidden")
        shown = list(shown) if isinstance(shown, (list, tuple)) else []
        hidden = list(hidden) if isinstance(hidden, (list, tuple)) else []
        title = STAGE_TITLE[key]
        tier = STAGE_TIER[key]
        rows = "".join(f"<li>{htmlmod.escape(s if isinstance(s, str) else str(s))}</li>"
                       for s in shown)
        hide_note = ""
        if hidden:
            hide_note = (f"<p><small>You hide "
                         f"{len(hidden)} step(s) — recall before peeking.</small></p>")
        return (
            f"<details class='fade-{key}'><summary>"
            f"<span class='fade-tag'>{htmlmod.escape(title)}</span> "
            f"<span class='hint-tag'>{htmlmod.escape(tier)}</span></summary>"
            f"<ol>{rows}</ol>{hide_note}</details>"
        )
    except Exception:  # noqa: BLE001 — renderer must never raise
        return ""


def fading_html(seq) -> str:
    """Escaped details/summary markup for a fade sequence; never raises.

    Empty or hostile input renders "".
    """
    try:
        if not isinstance(seq, (list, tuple)) or not seq:
            return ""
        parts = [_stage_html(item) for item in seq]
        body = "".join(parts)
        if not body:
            return ""
        return f"<div id='fading'>{body}</div>"
    except Exception:  # noqa: BLE001 — renderer must never raise
        return ""


def tour_entry() -> dict:
    """Tour registry entry for worked-example fading; never raises."""
    try:
        return {"id": "worked-fading", "kind": "feature",
                "title": "Worked-example fading",
                "blurb": "Worked traces fade per concept: full trace, "
                         "then the last step hides, then only the first "
                         "shows — recall grows as support shrinks.",
                "path": "/status", "anchor": STATUS_ANCHOR}
    except Exception:  # noqa: BLE001 — registry must never raise
        return {"id": "worked-fading", "kind": "feature",
                "title": "Worked-example fading",
                "blurb": "Worked examples fade from full to solo.",
                "path": "/status", "anchor": "status-b12-fading"}


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Worked-example fading "
        "<small>(feature)</small></h3>"
        "<p>Each concept's worked trace fades full to partial to solo: "
        "all steps shown, then the last step hidden, then only the first "
        "step shown. Stages reuse the <code>hinttiers</code> vocabulary "
        "(full=worked, partial=pointer, solo=nudge) by name so styling "
        "stays single-sourced. <code>groundwork/fading.py</code> provides "
        "<code>fade_sequence()</code> (empty input fails closed to "
        "<code>[]</code>) and <code>fading_html()</code> (escaped "
        "<code>details</code>/<code>summary</code> markup); library only, "
        "never raises, no pipeline or grading changes.</p>"
    )
