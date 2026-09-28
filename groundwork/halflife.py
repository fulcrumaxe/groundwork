"""Team knowledge half-life report (F-182): what decayed since last quarter.

Per-concept half-life derived from the FSRS-lite curve shared with
``sched.retrievability``: ``R(t) = (1+t/9S)^-1`` reaches one-half recall
at ``t = 9S``, so a concept's half-life is nine times its mean card
stability. Current recall uses days-since-last-review as ``t`` per
decision 281 (overdue-based elapsed would understate decay for
long-idle cards). A concept is flagged decayed when a card last seen
a quarter (90 days) or more ago sits below half recall today.

Pure renderer over a database path — ``history.history_html`` joins
``section_html`` next to the time ledger. Returns ``""`` until some
review is a quarter old, so histories without quarterly data render
exactly as before. Stdlib only; never raises.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import sched as schedmod

HALFLIFE_ANCHOR = "half-life"
STATUS_ANCHOR = "status-b29-halflife"

QUARTER_DAYS = 90
RECALL_FLOOR = 0.5
HALF_LIFE_FACTOR = 9.0


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _day(stamp) -> str:
    try:
        return str(stamp or "").strip()[:10]
    except Exception:  # noqa: BLE001 -- hostile stamp, caller decides
        return ""


def half_life_days(stability) -> float:
    """Days until recall halves at stability S (9*S); 0.0 on bad input."""
    stab = _num(stability)
    if stab is None or stab <= 0:
        return 0.0
    return HALF_LIFE_FACTOR * stab


def elapsed_days(reviewed_at, now: str = "") -> float | None:
    """Days since a review stamp (floor 0); None when undatable."""
    try:
        from datetime import date, datetime, timezone
        start = date.fromisoformat(_day(reviewed_at))
        end = (date.fromisoformat(_day(now)) if _day(now)
               else datetime.now(timezone.utc).date())
        return max(0.0, float((end - start).days))
    except Exception:  # noqa: BLE001 -- bad stamp means no t
        return None


def current_recall(stability, reviewed_at, now: str = "") -> float | None:
    """Recall today off days-since-last-review; None when undatable."""
    stab = _num(stability)
    lag = elapsed_days(reviewed_at, now)
    if stab is None or lag is None:
        return None
    try:
        return schedmod.retrievability(stab, lag)
    except Exception:  # noqa: BLE001 -- sched fallback is the same curve
        if stab <= 0:
            return 0.0
        return (1.0 + lag / (HALF_LIFE_FACTOR * stab)) ** -1


def _clean(rows):
    """[(concept, stability, reviewed_at)] dated-or-not card facts."""
    facts = []
    try:
        for row in rows or []:
            try:
                if isinstance(row, dict):
                    concept = row.get("concept", "")
                    stab = row.get("stability")
                    when = row.get("reviewed_at", "")
                else:
                    concept, stab, when = row[0], row[1], row[2]
            except (TypeError, IndexError, KeyError):
                continue
            stab = _num(stab)
            if not concept or stab is None:
                continue
            facts.append((str(concept), stab, when))
    except Exception:  # noqa: BLE001 -- hostile rows, keep what parsed
        pass
    return facts


def summarize(rows, now: str = "") -> dict:
    """Per-concept {half_life, recall, last_seen, decayed}; {} when none.

    Half-life needs only stability, so undated cards still count toward
    it; recall and the decayed flag need a review date and skip undated
    cards. Recall is the concept's worst card — one slipped card names
    the concept. Never raises.
    """
    try:
        by_concept: dict = {}
        for concept, stab, when in _clean(rows):
            slot = by_concept.setdefault(concept, {"stabs": [], "dated": []})
            slot["stabs"].append(stab)
            lag = elapsed_days(when, now)
            if lag is None:
                continue
            slot["dated"].append((when, lag, current_recall(stab, when, now)))
        out = {}
        for concept, slot in by_concept.items():
            stabs = slot["stabs"]
            half = (HALF_LIFE_FACTOR * sum(stabs) / len(stabs)) if stabs else 0.0
            dated = slot["dated"]
            if not dated:
                out[concept] = {"half_life": half, "recall": None,
                                "last_seen": "", "decayed": False}
                continue
            recall = min(r for _, _, r in dated)
            last_seen = max(str(w or "") for w, _, _ in dated)
            decayed = any(lag >= QUARTER_DAYS and r < RECALL_FLOOR
                          for _, lag, r in dated)
            out[concept] = {"half_life": half, "recall": recall,
                            "last_seen": last_seen, "decayed": decayed}
        return out
    except Exception:  # noqa: BLE001 -- summary never raises
        return {}


def decayed_since_quarter(rows, now: str = "") -> list:
    """Decayed concepts worst-first; [] with no quarterly decay."""
    try:
        flagged = [(c, s) for c, s in summarize(rows, now).items()
                   if s["decayed"]]
        flagged.sort(key=lambda kv: (kv[1]["recall"] is None,
                                     kv[1]["recall"] or 0.0))
        return [{"concept": c, **s} for c, s in flagged]
    except Exception:  # noqa: BLE001
        return []


def _card_facts(db_path: str) -> list:
    """(concept, stability, latest reviewed_at) per card; [] on failure."""
    try:
        con = dbmod.connect(db_path)
        try:
            return [(r["concept"], r["stability"], r["reviewed_at"]) for r in
                    con.execute(
                        "SELECT concepts.name AS concept,"
                        " cards.stability AS stability,"
                        " MAX(reviews.reviewed_at) AS reviewed_at"
                        " FROM cards JOIN concepts"
                        " ON concepts.id = cards.concept_id"
                        " LEFT JOIN reviews ON reviews.card_id = cards.id"
                        " GROUP BY cards.id").fetchall()]
        finally:
            con.close()
    except Exception:  # noqa: BLE001 -- report never breaks History
        return []


def section_html(db_path: str, now: str = "") -> str:
    """Quarterly decay report; "" until some review is a quarter old."""
    try:
        rows = _card_facts(db_path)
        if not any((elapsed_days(when, now) or -1) >= QUARTER_DAYS
                   for _, _, when in _clean(rows)):
            return ""
        summary = summarize(rows, now)
        decayed = [e for e in decayed_since_quarter(rows, now)]
        stable = len(summary) - len(decayed)
        head = (f"<h2 id='{HALFLIFE_ANCHOR}'>Knowledge half-life</h2>")
        if not decayed:
            return (head + f"<p>Nothing decayed since last quarter — "
                    f"{stable} concept{'s' if stable != 1 else ''} hold "
                    f"above half recall. The queue keeps no grudges.</p>")
        lines = "".join(
            f"<tr><td>{html.escape(e['concept'])}</td>"
            f"<td>{e['half_life']:.0f}d</td>"
            f"<td>{e['recall']:.0%}</td>"
            f"<td>{html.escape(_day(e['last_seen']))}</td></tr>"
            for e in decayed)
        return (
            head + f"<p>{len(decayed)} concept{'s' if len(decayed) != 1 else ''} "
            f"slipped below half recall since last quarter — review time "
            f"goes here first. {stable} still hold. Half-life is days until "
            f"recall halves at current stability.</p>"
            "<table class='log'><tr><th>Concept</th><th>Half-life</th>"
            "<th>Recall now</th><th>Last seen</th></tr>"
            f"{lines}</table>")
    except Exception:  # noqa: BLE001 -- History must never break
        return ""


def status_html(db_path: str = "") -> str:
    """Anchored status subsection with live decay counts."""
    try:
        rows = _card_facts(db_path) if db_path else []
        summary = summarize(rows)
        decayed = sum(1 for s in summary.values() if s["decayed"])
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Knowledge half-life "
            "<small>(feature)</small></h3>"
            "<p>What decayed since last quarter: per-concept half-life "
            "(nine times mean stability) plus the slipped list, rendered "
            "on History. <code>groundwork/halflife.py</code> flags a "
            "concept when a card last seen 90+ days ago sits below half "
            "recall. "
            f"Live: {decayed} decayed of {len(summary)} tracked.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Knowledge half-life</h3>"
                "<p>Half-life report temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    # Parent fix (Batch 19/F-178 precedent): the live report only
    # renders with quarter-old reviews, so the tour points at the
    # always-rendered Status section instead of /reviews (the tour
    # gate renders young fixtures).
    return {
        "id": "knowledge-half-life",
        "kind": "feature",
        "title": "Knowledge half-life",
        "blurb": "What decayed since last quarter — per-concept half-life "
                 "plus the slipped list, so review time goes where it matters.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
