"""Explain-differently order toggle (I-102).

One lesson, two orders: definition-first (legacy default) or example-first
(?order=examples). A pure render-time view over the same level blocks, so both
orders contain identical content — no stored second copy, no DB/schema change.
Stdlib only (html), no I/O, never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b18-explainflip"

ORDER_DEFINITION = "definition"
ORDER_EXAMPLES = "examples"

EXAMPLE_HEADS = frozenset({"See it happen", "Worked example", "Measured run"})


def normalize_order(value) -> str:
    """Canonical order; unknown/blank/hostile falls back to definition-first."""
    try:
        v = str(value).strip().lower() if value is not None else ""
    except Exception:
        return ORDER_DEFINITION
    if v in ("examples", "example", "example-first"):
        return ORDER_EXAMPLES
    return ORDER_DEFINITION


def is_example(block) -> bool:
    """True when a level block {h, b} is an example-kind (narrated) block."""
    try:
        return isinstance(block, dict) and str(block.get("h") or "") in EXAMPLE_HEADS
    except Exception:
        return False


def reorder_blocks(blocks, order=ORDER_DEFINITION) -> list:
    """Stable reorder: definition-first keeps legacy order; examples-first
    moves example-kind blocks front, relative order kept in both groups.
    A leading non-example block (the "Recall first" retrieval probe)
    stays pinned first so retrieval-first template enforcement holds.
    Unknown/hostile input returns the blocks unchanged (legacy fallback)."""
    try:
        if not isinstance(blocks, list) or not blocks:
            return blocks
        if normalize_order(order) != ORDER_EXAMPLES:
            return list(blocks)
        examples = [b for b in blocks if is_example(b)]
        if not examples or len(examples) == len(blocks):
            return list(blocks)
        rest = [b for b in blocks if not is_example(b)]
        if not is_example(blocks[0]):
            return [blocks[0]] + examples + rest[1:]
        return examples + rest
    except Exception:
        try:
            return list(blocks) if isinstance(blocks, list) else blocks
        except Exception:
            return blocks


def toggle_html(base_path: str, level: str = "auto", order=ORDER_DEFINITION) -> str:
    """Two-link order toggle preserving the level param; marks current order."""
    try:
        base = html.escape(str(base_path or "/"), quote=True)
        lv = html.escape(str(level or "auto"), quote=True)
        cur = normalize_order(order)
        parts = []
        for value, label in ((ORDER_DEFINITION, "Definition first"),
                             (ORDER_EXAMPLES, "Example first")):
            mark = " <b>(you are here)</b>" if value == cur else ""
            parts.append(f"<a href='{base}?level={lv}&order={value}'>{label}</a>{mark}")
        return f"<p><small>Explain it differently: {' · '.join(parts)}</small></p>"
    except Exception:
        return ""


def section_html() -> str:
    """Status-page subsection with a live both-orders demo."""
    try:
        demo = [
            {"h": "What it does", "b": "Backoff doubles the sleep after each failure."},
            {"h": "Worked example", "b": "For example: running retry() gives 4s on the third sleep."},
        ]
        def_first = " → ".join(b["h"] for b in reorder_blocks(demo, ORDER_DEFINITION))
        ex_first = " → ".join(b["h"] for b in reorder_blocks(demo, ORDER_EXAMPLES))
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Explain it differently <small>(improvement)</small></h3>"
            "<p>Lessons now read both ways: <code>groundwork/explainflip.py</code> "
            "reorders the same level blocks at render time — "
            "<code>?order=definition</code> (default) or <code>?order=examples</code> — "
            "with identical content in both orders and no stored copy.</p>"
            f"<p><small>Default: {html.escape(def_first)}<br>"
            f"Example-first: {html.escape(ex_first)}</small></p>")
    except Exception:
        return f"<h3 id='{STATUS_ANCHOR}'>Explain it differently <small>(improvement)</small></h3>"


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "explain-differently",
        "kind": "improvement",
        "title": "Explain it differently",
        "blurb": "Flip any lesson example-first or definition-first — same content, the order that clicks.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
