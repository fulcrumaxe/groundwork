"""'Try it yourself' micro-prompts between study paragraphs (I-112).

One rotating restate/exemplify/predict nudge after eligible prose
blocks -- never after recall questions, code blocks, or the last
block. Ungraded by design (no grade handling, no POST, no DB).
Stdlib only (`html`); never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b19-tryprompts"

TEMPLATES = (
    "Try it yourself: restate the idea above in one sentence, then check it against the next paragraph.",
    "Try it yourself: invent a tiny example of the idea above before reading on.",
    "Try it yourself: what would you predict the next paragraph says? Read on and compare.",
)

SKIP_HEADS = frozenset({"Recall first", "Worth probing"})


def prompt_for(index) -> str:
    """One rotating template for a block position; never raises."""
    try:
        i = int(index)
    except (TypeError, ValueError):
        return TEMPLATES[0]
    try:
        return TEMPLATES[i % len(TEMPLATES)]
    except Exception:  # noqa: BLE001
        return TEMPLATES[0]


def _eligible(block) -> bool:
    try:
        if not isinstance(block, dict):
            return False
        if block.get("pre"):
            return False
        body = block.get("b")
        if not isinstance(body, str) or not body.strip():
            return False
        return block.get("h") not in SKIP_HEADS
    except Exception:  # noqa: BLE001
        return False


def prompts_for(blocks) -> list:
    """One {"after", "prompt"} per eligible prose block, never the last."""
    try:
        if not isinstance(blocks, list) or not blocks:
            return []
        out = []
        for i, blk in enumerate(blocks):
            if i >= len(blocks) - 1:
                break
            if _eligible(blk):
                out.append({"after": i, "prompt": prompt_for(i)})
        return out
    except Exception:  # noqa: BLE001 -- selection never raises
        return []


def block_prompt_html(index, block) -> str:
    """Single inline nudge for one block; "" when ineligible."""
    try:
        if not _eligible(block):
            return ""
        try:
            i = int(index)
        except (TypeError, ValueError):
            i = 0
        return (
            "<details class='tryprompt'><summary>Try it yourself</summary>"
            f"<p>{html.escape(prompt_for(i))}</p></details>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def prompts_html(prompts) -> str:
    """Batch renderer for prompt dicts (status demo + tests)."""
    try:
        if not isinstance(prompts, list) or not prompts:
            return ""
        items = []
        for p in prompts:
            if not isinstance(p, dict):
                continue
            text = p.get("prompt")
            if not isinstance(text, str) or not text.strip():
                continue
            items.append(
                "<details class='tryprompt'><summary>Try it yourself</summary>"
                f"<p>{html.escape(text.strip())}</p></details>")
        if not items:
            return ""
        return f"<div id='tryprompts'>{''.join(items)}</div>"
    except Exception:  # noqa: BLE001
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch19 home module."""
    sample = prompts_html([{"after": 0, "prompt": prompt_for(0)}])
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Try-it-yourself micro-prompts <small>(improvement)</small></h3>"
        "<p>Study paragraphs pause for a try-it-yourself nudge — restate, "
        "exemplify, or predict before reading on. "
        "<code>groundwork/tryprompts.py</code> picks one rotating prompt per "
        "eligible prose block on the lesson rendering path "
        "(<code>lessons.render_levels</code>); recall questions, code blocks, "
        "and the final paragraph never take one, and nothing is graded. A "
        "live sample renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "try-prompts",
        "kind": "improvement",
        "title": "Try-it-yourself prompts",
        "blurb": "Study paragraphs pause for a try-it-yourself nudge — "
                 "restate, exemplify, or predict before reading on.",
        "path": "/modules/{mid}",
        "anchor": "{lesson}",
    }
