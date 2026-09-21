"""Interleaving engine v2 (F-61): concept × type matrix scheduler.

Blocked practice (ten retry cards in a row) feels fluent and teaches
nothing about *which* tool to reach for. Interleaving fixes the
choice: each pick is the weakest cell in the concept × exercise-type
matrix that does not repeat the previous pick's concept, so neighbors
always contrast. Ties break by input order (stable, explainable).

A cell is ``(concept, type, mastery)`` with mastery 0..1 (anything
unparseable fails closed to 0 — unknown means unpracticed, never
mastered). ``is_interleaved`` audits a finished sequence. Db-free
library — ``sched.py`` is untouched; pure functions, stdlib only, no
I/O, no DB changes.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b13-interleave"


def clean_cells(cells) -> list[tuple[str, str, float]]:
    """Usable cells: named concept+type, mastery clamped 0..1."""
    out = []
    try:
        for cell in cells or []:
            try:
                concept, kind, mastery = cell
                concept = str(concept).strip()
                kind = str(kind).strip()
                mastery = float(mastery)
            except Exception:  # noqa: BLE001 -- bad cell, skip it
                continue
            if not concept or not kind:
                continue
            if mastery != mastery:  # NaN: unknown, never mastered
                mastery = 0.0
            out.append((concept, kind,
                        min(1.0, max(0.0, mastery))))
        return out
    except Exception:  # noqa: BLE001 -- scheduler must never raise
        return []


def schedule(cells, n: int = 6) -> list[tuple[str, str, float]]:
    """Next ``n`` practice picks, weakest-first with no same-concept run.

    Greedy: take the lowest-mastery cell whose concept differs from
    the last pick; when every remaining cell repeats the concept
    (single-concept matrix), contrast is impossible and the weakest
    goes anyway. ``n`` clamps to 1..24; never raises.
    """
    try:
        pool = clean_cells(cells)
        try:
            count = int(n)
        except Exception:  # noqa: BLE001 -- count must never raise
            count = 6
        count = min(24, max(1, count))
        picks: list[tuple[str, str, float]] = []
        remaining = list(pool)
        while remaining and len(picks) < count:
            last = picks[-1][0] if picks else None
            cand = [c for c in remaining if c[0] != last] or remaining
            nxt = min(cand, key=lambda c: (c[2], pool.index(c)))
            picks.append(nxt)
            remaining.remove(nxt)
        return picks
    except Exception:  # noqa: BLE001 -- scheduler must never raise
        return []


def is_interleaved(seq) -> bool:
    """True when no two adjacent picks share a concept (vacuously true
    under two picks, or when the matrix holds one concept)."""
    try:
        items = list(seq or [])
        concepts = {c[0] for c in items}
        if len(items) < 2 or len(concepts) < 2:
            return True
        return all(items[i][0] != items[i + 1][0]
                   for i in range(len(items) - 1))
    except Exception:  # noqa: BLE001 -- audit must never raise
        return False


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    demo = schedule([("retry", "predict", 0.2), ("retry", "author", 0.8),
                     ("cache", "predict", 0.4), ("cache", "author", 0.6)], 4)
    rows = "".join(f"<tr><td>{c}</td><td>{t}</td><td>{m:.1f}</td></tr>"
                   for c, t, m in demo)
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Interleaving engine <small>(feature)</small></h3>"
        "<p>Practice now contrasts instead of blocking: "
        "<code>groundwork/interleave.py</code> provides "
        "<code>schedule()</code> (weakest concept × type cell that does "
        "not repeat the last concept — neighbors always differ) and "
        "<code>is_interleaved()</code> (sequence audit), a db-free "
        "library that leaves <code>sched.py</code> untouched. Four "
        "sample picks render below.</p>"
        "<table class='log'><tr><th>Concept</th><th>Type</th>"
        f"<th>Mastery</th></tr>{rows}</table>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "interleaving",
        "kind": "feature",
        "title": "Interleaving engine",
        "blurb": "Practice picks contrast by concept — weakest cell first, never the same idea twice running.",
        "path": "/status",
        "anchor": "status-b13-interleave",
    }
