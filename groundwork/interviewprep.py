"""Pre-interview confidence builder (F-134): targeted recap track.

Capped weakest-first queue slice over known concepts: lowest mastery
first, stalest due date breaks ties, concept id breaks the rest. Pure
functions of passed-in dicts, stdlib only, no I/O, no DB. Caller:
Handler.due_html beside the serendipity bonus. Empty pool renders ""
so legacy bytes survive. Never raises; never mutates inputs.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b25-interviewprep"
SECTION_ANCHOR = "preptrack"
DEFAULT_SIZE = 5
MAX_SIZE = 12
_MISSING_DUE = "\uffff"


def _mastery(row) -> float:
    try:
        m = float((row or {}).get("mastery") or 0.0)
        return m if m == m else 0.0  # NaN is weakest, never crashes sort
    except (TypeError, ValueError):
        return 0.0


def _earliest_due(due) -> dict:
    """concept_id -> earliest due iso; hostile cards skipped."""
    out: dict = {}
    try:
        cards = list(due or [])
    except TypeError:
        return {}
    for c in cards:
        if not isinstance(c, dict):
            continue
        cid = c.get("concept_id")
        cid = str(cid).strip() if cid is not None else ""
        d = c.get("due")
        d = d if isinstance(d, str) and d else ""
        if cid and d and d < out.get(cid, _MISSING_DUE):
            out[cid] = d
    return out


def _size_of(size) -> int:
    try:
        return max(0, min(int(size), MAX_SIZE))
    except (TypeError, ValueError):
        return DEFAULT_SIZE


def pick_track(concepts, due=None, size=DEFAULT_SIZE) -> list:
    """Up to `size` concept dicts, weakest mastery first.

    Each pick: {concept_id, name, module_id, mastery, due, reason}.
    Missing mastery counts as 0.0 (unknown surfaces); concepts with
    no due card sort after dated ones within a mastery tier. Empty or
    hostile input yields []. Never raises; never mutates inputs.
    """
    try:
        want = _size_of(size)
        edue = _earliest_due(due)
        seen: set = set()
        pool = []
        for r in (concepts or []):
            if not isinstance(r, dict):
                continue
            cid = r.get("id", r.get("concept_id"))
            cid = str(cid).strip() if cid is not None else ""
            if not cid or cid in seen:
                continue
            seen.add(cid)
            m = _mastery(r)
            d = edue.get(cid, "")
            pool.append((m, d or _MISSING_DUE, cid, r))
        pool.sort(key=lambda t: (t[0], t[1], t[2]))
        out = []
        for m, _, cid, r in pool[:want]:
            name = r.get("name") or cid
            d = edue.get(cid, "")
            reason = f"mastery {m:.2f}" + (f" · due {d[:10]}" if d else "")
            out.append({"concept_id": cid, "name": str(name),
                        "module_id": str(r.get("module_id") or ""),
                        "mastery": m, "due": d, "reason": reason})
        return out
    except Exception:  # noqa: BLE001 -- picker never raises
        return []


def track_html(concepts, due=None, size=DEFAULT_SIZE) -> str:
    """Due-page recap box; "" when nothing is known (legacy fallback)."""
    try:
        picks = pick_track(concepts, due, size)
        if not picks:
            return ""
        from . import lessons as lesmod
        lis = []
        for p in picks:
            mid, name = p["module_id"], p["name"]
            href = (f"/modules/{mid}#lesson-{lesmod.slug(name)}"
                    if mid else "/modules")
            lis.append(
                f"<li>{html.escape(name)} "
                f"<small>{html.escape(p['reason'])}</small> — "
                f"<a href='{html.escape(href, True)}'>Study</a></li>")
        n = len(picks)
        return (
            f"<section id='{SECTION_ANCHOR}'><h2>Interview recap track</h2>"
            f"<p>{n} shakiest idea{'s' if n != 1 else ''} — "
            f"recap before the interview.</p><ol>{''.join(lis)}</ol></section>")
    except Exception:  # noqa: BLE001 -- box never breaks Due
        return ""


def tour_entry() -> dict:
    """Tour registry entry for the pre-interview recap track."""
    return {"id": "interview-recap-track", "kind": "feature",
            "title": "Pre-interview recap track",
            "blurb": ("Your shakiest ideas first, capped with study "
                      "links — recap before the interview."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch25.py."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Pre-interview recap track "
        "<small>(feature)</small></h3>"
        "<p>Weakest mastery first, stalest due date breaks ties — a "
        "capped track with study links beside the Due queue. "
        "<code>groundwork/interviewprep.py</code> provides "
        "<code>pick_track()</code> and <code>track_html()</code> "
        "(empty pool renders nothing, legacy bytes survive).</p>")
