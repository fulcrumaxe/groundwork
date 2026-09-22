"""Pinned lessons (I-117): must-read lessons stay atop the module.

A pin list names lessons (concept id, node name, or display name);
``order_with_pins`` stably partitions them first in pin order while
every other lesson keeps its relative order. An empty or unknown pin
list returns the input order untouched, so pages without pins render
byte-identical to the legacy path. Stdlib only (``html``); no I/O,
never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b20-lessonpin"


def normalize_pins(pins) -> list:
    """Deduped non-empty string pins; [] for missing/hostile input."""
    try:
        if pins is None or isinstance(pins, str):
            return []
        out = []
        for pin in pins:
            if isinstance(pin, str) and pin.strip() and pin not in out:
                out.append(pin)
        return out
    except Exception:  # noqa: BLE001 -- normalizing never raises
        return []


def _node_key(item) -> list:
    """Candidate pin keys for a concept row or lesson dict."""
    try:
        keys = []
        if isinstance(item, dict):
            get = item.get
        else:
            def get(name, default=""):
                try:
                    return item[name]
                except (KeyError, IndexError, TypeError):
                    return default
        for name in ("cid", "concept_id", "name"):
            value = get(name, "")
            if isinstance(value, str) and value.strip():
                keys.append(value)
                if ":" in value:
                    keys.append(value.split(":", 1)[1])
        return keys
    except Exception:  # noqa: BLE001
        return []


def is_pinned(item, pins) -> bool:
    """True iff any pin names this lesson; False on hostile input."""
    try:
        wanted = normalize_pins(pins)
        if not wanted:
            return False
        keys = set(_node_key(item))
        return any(pin in keys for pin in wanted)
    except Exception:  # noqa: BLE001
        return False


def order_with_pins(items, pins) -> list:
    """Pinned-first stable partition; input order back when no pins hit.

    Never mutates the input, never raises; non-list input yields [].
    """
    try:
        if not isinstance(items, list):
            return []
        wanted = normalize_pins(pins)
        if not wanted:
            return list(items)
        rank = {pin: i for i, pin in enumerate(wanted)}
        def _rank(item):
            hits = [rank[k] for k in _node_key(item) if k in rank]
            return min(hits) if hits else None
        pinned = sorted(
            (it for it in items if _rank(it) is not None),
            key=_rank)
        rest = [it for it in items if _rank(it) is None]
        return pinned + rest if pinned else list(items)
    except Exception:  # noqa: BLE001
        try:
            return list(items)
        except Exception:  # noqa: BLE001
            return []


def pin_marker_html(item, pins) -> str:
    """' Pinned' chip for pinned lessons; "" otherwise (legacy bytes)."""
    try:
        if not is_pinned(item, pins):
            return ""
        return " <span class='pin'>Pinned</span>"
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def pin_css() -> str:
    """Raw declarations only (no <style> tags); palette tokens."""
    return (".pin{font-size:smaller;color:var(--ink);"
            "background:var(--paper);padding:0 4px;}")


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    sample = "".join(
        f"<li>{html.escape(name)}{pin_marker_html({'name': name}, ['b'])}</li>"
        for name in ("a", "b", "c"))
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Pinned lessons <small>(improvement)</small></h3>"
        "<p>Pin must-read lessons so they stay atop the module no matter "
        "how the list is ordered. <code>groundwork/lessonpin.py</code> "
        "stably partitions pinned lessons first on the module rendering "
        "path (<code>Handler.module_html</code>); pages without pins "
        "render exactly as before. Pinned rows carry a marker:</p>"
        f"<ul>{sample}</ul>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "pinned-lessons",
        "kind": "improvement",
        "title": "Pinned lessons",
        "blurb": "Pin must-read lessons so they stay atop the module "
                 "no matter how the list is ordered.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
