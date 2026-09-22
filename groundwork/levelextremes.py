"""Explainer level extremes (I-123): ELI5 analogy on top, tradeoffs below.

``explain.levels_for``/``auto_level`` hard-code levels 1-4, so the L1
"ELI5" and L5 "design tradeoffs" extremes ride alongside as optional
blocks: an ELI5 analogy from the lesson's ``eli5`` mapping, and a
tradeoff contract/alternatives/probe from its ``tradeoffs`` list.
Lessons without that data render ("", "") and the lesson path stays
byte-identical. Stdlib only (``html``); no I/O, never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b20-levelextremes"

MAX_ALTERNATIVES = 3


def _text(value) -> str:
    try:
        return value.strip() if isinstance(value, str) else ""
    except Exception:  # noqa: BLE001
        return ""


def eli5_for(lesson) -> dict:
    """{"analogy", "takeaway"} from lesson["eli5"]; {} when absent."""
    try:
        if not isinstance(lesson, dict):
            return {}
        raw = lesson.get("eli5")
        if not isinstance(raw, dict):
            return {}
        analogy, takeaway = _text(raw.get("analogy")), _text(raw.get("takeaway"))
        if not analogy or not takeaway:
            return {}
        return {"analogy": analogy, "takeaway": takeaway}
    except Exception:  # noqa: BLE001
        return {}


def tradeoffs_for(lesson) -> dict:
    """{"contract", "alternatives", "probe"}; {} unless alternatives exist.

    The contract is the lesson summary's first line; alternatives come
    from the lesson's ``tradeoffs`` list (capped); the probe names the
    lesson's concept. Never invents alternatives. Never raises.
    """
    try:
        if not isinstance(lesson, dict):
            return {}
        alts = [a.strip() for a in (lesson.get("tradeoffs") or [])
                if isinstance(a, str) and a.strip()][:MAX_ALTERNATIVES]
        if not alts:
            return {}
        summary = lesson.get("summary")
        contract = (summary.splitlines()[0][:200]
                    if isinstance(summary, str) and summary.strip() else "")
        name = lesson.get("name")
        probe = (f"When would you avoid {_text(name) or 'this'}?")
        return {"contract": contract, "alternatives": alts, "probe": probe}
    except Exception:  # noqa: BLE001
        return {}


def eli5_html(data: dict) -> str:
    """ELI5 block; "" on empty/hostile input."""
    try:
        if not isinstance(data, dict) or not data.get("analogy") \
                or not data.get("takeaway"):
            return ""
        return (
            "<aside class='extremes-eli5'><h5>Explain it like I'm five</h5>"
            f"<p>{html.escape(data['analogy'])}</p>"
            f"<p><small>Takeaway: {html.escape(data['takeaway'])}</small></p></aside>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def tradeoffs_html(data: dict) -> str:
    """Tradeoffs block; "" on empty/hostile input."""
    try:
        if not isinstance(data, dict) or not data.get("alternatives"):
            return ""
        alts = "".join(f"<li>{html.escape(a)}</li>"
                       for a in data["alternatives"][:MAX_ALTERNATIVES])
        contract = html.escape(data.get("contract") or "")
        probe = html.escape(data.get("probe") or "")
        return (
            "<aside class='extremes-tradeoffs'><h5>Design tradeoffs</h5>"
            f"<p>{contract}</p><ul>{alts}</ul>"
            f"<p><small>{probe}</small></p></aside>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def extreme_blocks(lesson) -> tuple:
    """(top, bottom) extreme blocks; ("", "") with no extreme data."""
    try:
        return (eli5_html(eli5_for(lesson)),
                tradeoffs_html(tradeoffs_for(lesson)))
    except Exception:  # noqa: BLE001
        return ("", "")


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    sample = (eli5_html({"analogy": "Like a piggy bank that only takes twos.",
                         "takeaway": "Defaults do the adding."})
              + tradeoffs_html({"contract": "Totals two numbers.",
                                "alternatives": ["Inline the sum",
                                                 "Use a running total"],
                                "probe": "When would you avoid add()?"}))
    return (
        f"<h3 id='{STATUS_ANCHOR}'>ELI5 and tradeoff extremes <small>(improvement)</small></h3>"
        "<p>Explainers stretch both ways: an ELI5 analogy on top, design "
        "tradeoffs below — without touching the level 1-4 tabs. "
        "<code>groundwork/levelextremes.py</code> renders these sidecar "
        "blocks on the lesson rendering path "
        "(<code>lessons.render_levels</code>) only when the lesson "
        "carries the data; otherwise the page is byte-identical. Live "
        "samples render below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "level-extremes",
        "kind": "improvement",
        "title": "ELI5 and tradeoff extremes",
        "blurb": "Explainers stretch both ways: an ELI5 analogy on top, "
                 "design tradeoffs below.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
