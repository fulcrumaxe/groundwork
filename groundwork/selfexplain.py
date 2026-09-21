"""Self-explanation prompts after every worked step (F-58).

After each worked line (a ``lesson["how"]`` walkthrough entry, or a
``lesson["worked"]["trace"]["steps"]`` value), the learner is asked
"why does this line exist?" in their own words — a retrieval nudge,
not a graded exercise.

LIBRARY ONLY: no pipeline/exercises/grading changes, no new exercise
type, no DB/schema changes. Callers pass a plain ``list[str]`` of
worked steps (the REAL step structure is ``lesson["how"]: list[str]``;
trace steps ``worked["trace"]["steps"]`` fit the same shape) and get
back one prompt dict per step. Stage names mirror the sibling fading
module's convention (``full``/``partial``/``solo``) by name only —
this module does NOT import it. Tier vocabulary follows
``hinttiers`` (these prompts sit at the ``worked`` end). Pure
functions, stdlib only (``html``), no I/O. Every public helper fails
closed and never raises.
"""
from __future__ import annotations

import html as htmlmod

STATUS_ANCHOR = "status-b12-selfexplain"

# Fading-stage names, mirrored by convention only (no import; the
# sibling F-57 module owns the real progression). Prompts are
# stage-agnostic: the parent decides when a step shows one.
STAGES = ("full", "partial", "solo")

TEMPLATES = (
    "Why does this line exist? What would break if step {n} were removed?",
    "What is step {n} for? Explain its purpose in your own words.",
    "Why does step {n} sit here? What does it set up for the next step?",
)


def prompt_for(index) -> str:
    """One rotating prompt template for a step position; never raises."""
    try:
        if isinstance(index, bool):
            return TEMPLATES[0].format(n=1)
        i = int(index)
        if i < 0:
            i = 0
        return TEMPLATES[i % len(TEMPLATES)].format(n=i + 1)
    except Exception:  # noqa: BLE001 — template lookup must never raise
        return TEMPLATES[0].format(n=1)


def selfexplain_prompts(steps) -> list:
    """One ``{"step": i, "prompt": str}`` per worked step.

    ``steps`` is the worked-step list (``lesson["how"]`` lines or
    ``worked["trace"]["steps"]`` values). Templates rotate by index so
    adjacent steps ask different "why" questions. Empty input, a
    non-list ``steps``, or non-string/blank entries fail closed (bad
    entries are skipped, never echoed); never raises.
    """
    try:
        if not isinstance(steps, (list, tuple)) or not steps:
            return []
        out = []
        for i, s in enumerate(steps):
            try:
                if not isinstance(s, str) or not s.strip():
                    continue
                out.append({"step": i, "prompt": prompt_for(i)})
            except Exception:  # noqa: BLE001 — one bad step skips, never raises
                continue
        return out
    except Exception:  # noqa: BLE001 — generator must never raise
        return []


def prompts_html(prompts) -> str:
    """Escaped ``<details>/<summary>`` markup for prompt dicts.

    Empty or hostile input renders ``""``; items without a usable
    prompt string are skipped; all text is ``html.escape``d. The
    wrapper carries ``id='selfexplain'`` so the tour entry has a
    stable target. Never raises.
    """
    try:
        if not isinstance(prompts, (list, tuple)) or not prompts:
            return ""
        parts = []
        for pos, item in enumerate(prompts):
            try:
                if not isinstance(item, dict):
                    continue
                text = item.get("prompt")
                if not isinstance(text, str) or not text.strip():
                    continue
                try:
                    n = int(item.get("step", pos)) + 1
                    if n < 1:
                        n = pos + 1
                except (TypeError, ValueError):
                    n = pos + 1
                parts.append(
                    "<details class='selfexplain'><summary>"
                    f"Step {n} — why does this line exist?</summary>"
                    f"<p>{htmlmod.escape(text)}</p></details>"
                )
            except Exception:  # noqa: BLE001 — one bad item skips, never raises
                continue
        if not parts:
            return ""
        return "<div id='selfexplain'>" + "".join(parts) + "</div>"
    except Exception:  # noqa: BLE001 — renderer must never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Self-explanation prompts <small>(feature)</small></h3>"
        "<p>Every worked step now asks <i>why does this line exist?</i> — "
        "one rotating retrieval nudge per <code>how</code>/trace line, answered "
        "in the learner's own words and never graded. "
        "<code>groundwork/selfexplain.py</code> provides "
        "<code>selfexplain_prompts()</code> (one "
        "<code>{step, prompt}</code> dict per step, templates rotating by "
        "index) and <code>prompts_html()</code> (escaped "
        "<code>&lt;details&gt;</code>/<code>&lt;summary&gt;</code> markup); "
        "library only — no pipeline, exercise, grading, DB, or schema "
        "changes — with fail-closed helpers that never raise. Stage names "
        "mirror the fading convention (<code>full</code>/<code>partial</code>/"
        "<code>solo</code>) without depending on it.</p>"
    )


def tour_entry() -> dict:
    """Tour registry entry for self-explanation prompts; never raises."""
    try:
        return {"id": "self-explain", "kind": "feature",
                "title": "Self-explanation prompts",
                "blurb": "Every worked step asks why it exists — explain each line in your own words before moving on.",
                "path": "/status", "anchor": STATUS_ANCHOR}
    except Exception:  # noqa: BLE001 — tour entry must never raise
        return {"id": "self-explain", "kind": "feature",
                "title": "Self-explanation prompts",
                "blurb": "Every worked step asks why it exists.",
                "path": "/status", "anchor": "status-b12-selfexplain"}
