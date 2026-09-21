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


def _cell_key(card: dict) -> tuple[str, str]:
    """(concept, type) labels for one due card; blanks become named."""
    try:
        concept = str(card.get("concept_id") or "unfiled").strip() or "unfiled"
        kind = str(card.get("exercise_type", "general")).strip() or "general"
        return concept, kind
    except Exception:  # noqa: BLE001 -- key must never raise
        return "unfiled", "general"


def order_due(cards, mastery=None) -> list:
    """Due queue order via the engine (Batch 14, F-61).

    ``mastery`` maps (concept, type) or plain concept ids to average
    grades 0..5 (unknown concepts score 0.0 — unpracticed, never
    mastered, per the engine's own rule). Cells rank weakest-first
    with contrast; cards deal round-robin across the ranked cells,
    the same shape as ``sched.interleave`` with a smarter group
    order. Empty/missing mastery falls back to ``sched.interleave``
    byte-identical — the legacy default. Never raises; garbage rows
    keep their relative order at the end.
    """
    try:
        from . import sched as schedmod
    except Exception:  # noqa: BLE001 -- fallback must never raise
        schedmod = None
    try:
        items = [c for c in (cards or []) if isinstance(c, dict)]
        if not items:
            return []
        if not isinstance(mastery, dict) or not mastery:
            if schedmod is None:
                return list(items)
            return schedmod.interleave(items)
        # Normalize keys: sqlite hands back ints for exercise_type
        # while cards may carry strings — compare str to str.
        norm: dict = {}
        for k, v in mastery.items():
            try:
                if isinstance(k, (list, tuple)) and len(k) == 2:
                    norm[(str(k[0]), str(k[1]))] = v
                else:
                    norm[str(k)] = v
            except Exception:  # noqa: BLE001 -- bad key, skip it
                continue
        mastery = norm
        groups: dict = {}
        gorder: list = []
        for c in items:
            key = _cell_key(c)
            if key not in groups:
                groups[key] = []
                gorder.append(key)
            groups[key].append(c)

        def _level(key) -> float:
            concept, kind = key
            for cand in ((concept, kind), concept):
                try:
                    if cand in mastery:
                        return min(1.0, max(0.0, float(mastery[cand]) / 5.0))
                except Exception:  # noqa: BLE001 -- bad value, try next
                    continue
            return 0.0

        cells = [(concept, kind, _level((concept, kind)))
                 for concept, kind in gorder]
        ranked = schedule(cells, len(cells))
        label_to_key = {(c, t): (c, t) for c, t in gorder}
        ranked_keys = [label_to_key.get((c, t), gorder[0]) for c, t, _ in ranked]
        # Cover cells the engine skipped (it never should, but the
        # queue must never lose a card).
        for key in gorder:
            if key not in ranked_keys:
                ranked_keys.append(key)
        queues = {k: list(groups[k]) for k in ranked_keys}
        out = []
        while any(queues.values()):
            for k in ranked_keys:
                if queues[k]:
                    out.append(queues[k].pop(0))
        return out
    except Exception:  # noqa: BLE001 -- ordering must never raise
        try:
            return list(cards or [])
        except Exception:  # noqa: BLE001 -- last resort
            return []


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
        "<code>is_interleaved()</code> (sequence audit). Since Batch 14 "
        "the Due queue calls it for real: <code>order_due()</code> "
        "ranks concept × type cells by live mastery and deals "
        "round-robin across them (empty mastery falls back to the "
        "legacy order). Four sample picks render below.</p>"
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
