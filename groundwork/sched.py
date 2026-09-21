"""FSRS-lite scheduler + review queue + staleness (PRD pipeline step 6).

Simplified FSRS: per-card stability S, difficulty D, retrievability R.
R(t) = (1 + t/(9*S))^-1  (FSRS-4.5 forgetting curve shape).
On review with grade g in 0..5:
  D' = D - 0.1*(g-3), clamped [0.1, 1.0]... (linearised; full FSRS uses
       a linear-damping ODE — this keeps monotonic behaviour)
  S' = S * (1 + e^(3-D) * (g-3) * 0.2 + 0.2) for g>=3, S * 0.5 for g<3.
Pass (g>=3) pushes the due date out; fail pulls it in.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def retrievability(stability: float, elapsed_days: float) -> float:
    if stability <= 0:
        return 0.0
    return (1.0 + elapsed_days / (9.0 * stability)) ** -1


def review_card(stability: float, difficulty: float, grade: int,
                now: datetime | None = None, grades=None) -> dict:
    """Apply one review. Returns {stability, difficulty, retrievability, due}.

    ``grades`` is the oldest-first grade history INCLUDING the current
    grade (Batch 14, F-62): the trailing pass streak stretches the due
    gap via the spacing optimizer, so strong concepts return later.
    ``None`` (or empty) means today's behavior exactly — the legacy
    default every existing caller relies on. The streak only ever
    stretches; collapse stays the stability model's job (halving on
    real fails), and pass here means grade >= 4 while the stability
    model moves at >= 3.
    """
    now = now or utcnow()
    g = max(0, min(5, grade))
    difficulty = min(1.0, max(0.1, difficulty - 0.1 * (g - 3)))
    if g >= 3:
        stability = max(0.1, stability * (1.0 + math.exp(3.0 - difficulty) * (g - 3) * 0.2 + 0.2))
    else:
        stability = max(0.1, stability * 0.5)
    interval = max(1, round(stability))
    if grades is not None:
        from . import spacingopt as spacingoptmod
        stretched = max(1, int(round(spacingoptmod.next_interval(
            grades, interval))))
        # The optimizer stretches, never shrinks: above its ceiling
        # the stability model's own (uncapped) gap still rules.
        interval = max(interval, stretched)
    due = now + timedelta(days=interval)
    return {"stability": stability, "difficulty": difficulty,
            "retrievability": 1.0, "due": iso(due)}


def forecast_gap(stability: float, streak: int = 0) -> str:
    """Next-gap estimate at steady passes, from stability (I-203).

    Mirrors the review_card interval so the Due forecast and the
    scheduler agree: max(1, round(stability)) days, stretched by the
    pass streak when one is given (Batch 14, F-62). The default call
    is byte-identical to before.
    """
    try:
        base = max(1, round(float(stability or 0.0)))
    except (TypeError, ValueError):
        return "unknown"
    try:
        n = max(0, int(streak))
    except (TypeError, ValueError):
        n = 0
    if n:
        from . import spacingopt as spacingoptmod
        base = max(1, int(round(spacingoptmod.apply_streak(float(base), n))))
    return f"≈{base}d"


def snooze_due(now: datetime | None = None) -> str:
    """Next-day due timestamp for a snoozed card (no grade recorded)."""
    return iso((now or utcnow()) + timedelta(days=1))


def elapsed_retrievability(stability: float, due_iso: str,
                           now: datetime | None = None) -> float:
    now = now or utcnow()
    try:
        due = parse_iso(due_iso)
    except ValueError:
        return 1.0
    elapsed = max(0.0, (now - due).total_seconds() / 86400.0)
    return retrievability(stability, elapsed)


def interleave(cards: list[dict]) -> list[dict]:
    """Round-robin across concepts so reviews mix topics (interleaving)."""
    by_concept: dict = {}
    order: list = []
    for c in cards:
        k = c.get("concept_id")
        if k not in by_concept:
            by_concept[k] = []
            order.append(k)
        by_concept[k].append(c)
    out: list[dict] = []
    while any(by_concept.values()):
        for k in order:
            if by_concept[k]:
                out.append(by_concept[k].pop(0))
    return out
