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
                now: datetime | None = None) -> dict:
    """Apply one review. Returns {stability, difficulty, retrievability, due}."""
    now = now or utcnow()
    g = max(0, min(5, grade))
    difficulty = min(1.0, max(0.1, difficulty - 0.1 * (g - 3)))
    if g >= 3:
        stability = max(0.1, stability * (1.0 + math.exp(3.0 - difficulty) * (g - 3) * 0.2 + 0.2))
    else:
        stability = max(0.1, stability * 0.5)
    interval = max(1, round(stability))
    due = now + timedelta(days=interval)
    return {"stability": stability, "difficulty": difficulty,
            "retrievability": 1.0, "due": iso(due)}


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
