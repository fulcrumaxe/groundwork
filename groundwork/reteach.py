"""Spaced teaching (F-90): re-teach a concept after 30 days.

Concepts first attempted 30+ days ago return to the Due queue beside
the learner's own first words (the earliest review submission), with
a fresh self-explain prompt to compare against. Fresh databases —
nothing old enough — render the Due queue byte-identical. Stdlib
only (``html``); no I/O, never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b20-reteach"

RETEACH_AFTER_DAYS = 30
QUOTE_CHARS = 280


def _days_since(first_seen: str, now: str = "") -> float | None:
    try:
        if not isinstance(first_seen, str) or not first_seen.strip():
            return None
        from datetime import date
        start = date.fromisoformat(first_seen.strip()[:10])
        end = date.fromisoformat(now.strip()[:10]) if (
            isinstance(now, str) and now.strip()) else date.today()
        return (end - start).days
    except Exception:  # noqa: BLE001
        return None


def due_for_reteach(first_seen_iso, now: str = "") -> bool:
    """True iff first seen 30+ days ago; False on hostile input."""
    try:
        elapsed = _days_since(first_seen_iso, now)
        return elapsed is not None and elapsed >= RETEACH_AFTER_DAYS
    except Exception:  # noqa: BLE001 -- fail closed
        return False


def first_attempts(rows) -> list:
    """[{name, first_seen, recording}] earliest row per concept name.

    Rows are mappings (or tuples) of (name, reviewed_at, submission),
    oldest-first wins. Never raises.
    """
    try:
        firsts: dict = {}
        for row in rows or []:
            try:
                if isinstance(row, dict):
                    name, when, sub = (row.get("name"), row.get("reviewed_at"),
                                       row.get("submission"))
                else:
                    name, when, sub = row[0], row[1], row[2]
            except (TypeError, IndexError, KeyError):
                continue
            name = str(name or "")
            stamp = str(when or "")
            if not name:
                continue
            prev = firsts.get(name)
            if prev is None or (stamp or "9999") < (prev["first_seen"] or "9999"):
                firsts[name] = {"name": name, "first_seen": stamp,
                                "recording": str(sub or "")}
        return list(firsts.values())
    except Exception:  # noqa: BLE001
        return []


def pick_reteach(rows, now: str = "") -> list:
    """Due rows oldest-first; [] on missing/hostile input."""
    try:
        due = [r for r in (rows or [])
               if isinstance(r, dict)
               and due_for_reteach(r.get("first_seen", ""), now)]
        due.sort(key=lambda r: str(r.get("first_seen", "")))
        return due
    except Exception:  # noqa: BLE001
        return []


def _words(text) -> set:
    try:
        return {w.strip(".,;:!?()[]{}\"'").lower() for w in str(text or "").split()
                if len(w.strip(".,;:!?()[]{}\"'")) > 2}
    except Exception:  # noqa: BLE001
        return set()


def compare_recordings(old, new) -> dict:
    """{shared, growth, verdict} word overlap; no-comparison when thin."""
    try:
        old_words, new_words = _words(old), _words(new)
        if not old_words or not new_words:
            return {"shared": [], "growth": 0, "verdict": "no-comparison"}
        shared = sorted(old_words & new_words)[:12]
        growth = len(new_words - old_words)
        verdict = "growing" if growth > 0 else "steady"
        return {"shared": shared, "growth": growth, "verdict": verdict}
    except Exception:  # noqa: BLE001
        return {"shared": [], "growth": 0, "verdict": "no-comparison"}


def reteach_box_html(items) -> str:
    """Re-teach box for due items; "" when none due."""
    try:
        rows = [it for it in (items or []) if isinstance(it, dict)]
        if not rows:
            return ""
        blocks = []
        for it in rows:
            name = str(it.get("name", "") or "this concept")
            quote = str(it.get("recording", "") or "")[:QUOTE_CHARS]
            block = (f"<h4>{html.escape(name)}</h4>"
                     f"<p><small>Your words from then:</small> "
                     f"<q>{html.escape(quote)}</q></p>"
                     f"<p>Explain {html.escape(name)} again in your own "
                     f"words — then compare.</p>")
            blocks.append(block)
        return f"<div id='reteach'><h3>Re-teach after 30 days</h3>{''.join(blocks)}</div>"
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    sample = reteach_box_html([{"name": "add",
                                "recording": "totals two numbers"}])
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Re-taught after 30 days <small>(feature)</small></h3>"
        "<p>A month-old concept returns with your own words beside a "
        "fresh prompt. <code>groundwork/reteach.py</code> watches first "
        "attempts on the Due queue (<code>Handler.due_html</code>); "
        "fresh databases see no box at all. A live sample renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "reteach-30d",
        "kind": "feature",
        "title": "Re-taught after 30 days",
        "blurb": "A month-old concept returns with your own words "
                 "beside a fresh prompt.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
