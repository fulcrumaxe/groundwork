"""Boredom detection: too-easy streak jumps one Bloom rung (F-97).

A learner who aces the last K reviews (grades >= 4, oldest-first history
including the current grade, the sched.review_card convention) at a low
Bloom rung is bored: the Due queue should offer the next rung up for that
concept instead of more same-level drills. Pure helpers, stdlib only, no
I/O, no DB or schema changes.

Caller path (Due queue, never a Status demo):
``MCPServer.tool_list_due_reviews`` groups recent grades per concept and
passes them with the ordered queue into ``promote``, which stably moves
a bored concept's suggested-rung cards first (thin delegation: order
only, dues and grades untouched). With no grade data every helper
returns its legacy value (not bored, same tier, "" badge, same order),
so calm queues render byte-identical.

Rung order is the canonical Bloom progression from
``debt.BLOOM_RUNGS`` (recall < explain < apply < analyse < modify <
create), shared with the debt ladder so both agree what "one rung up"
means. Two real card tiers sit off that ladder: ``understand`` (the
Batch-18 reading-fluency tier) resolves to recall, ``evaluate``
(code-review cards) to modify. Card tiers resolve from
``exercise_type`` via ``exercises.TYPES``. ``History`` may show
``badge_html`` beside the streak; the status section already samples
it below.
"""
from __future__ import annotations

import html as htmlmod

from .debt import BLOOM_RUNGS

STATUS_ANCHOR = "status-b21-boredom"

RUNGS = tuple(BLOOM_RUNGS)

# Off-ladder display tiers -> nearest canonical rung. Fluency sits at
# the base; review-style cards sit beside modify, one rung below create.
_OFF_LADDER = {"understand": "recall", "evaluate": "modify"}


def _canon(tier) -> str:
    """Tier key on the canonical ladder; "" when unknown. Never raises."""
    try:
        key = str(tier).strip().lower()
    except Exception:  # noqa: BLE001 -- coercion never raises
        return ""
    return _OFF_LADDER.get(key, key)

PASS_GRADE = 4
STREAK_N = 3
HISTORY_TAIL = 8


def rung_index(tier) -> int:
    """0-based canonical rung position, or -1 when unknown; never raises.

    Off-ladder tiers resolve to their nearest canonical rung
    (understand -> recall, evaluate -> modify).
    """
    try:
        key = _canon(tier)
        return RUNGS.index(key) if key in RUNGS else -1
    except Exception:  # noqa: BLE001 -- lookup never raises
        return -1


def next_rung(tier) -> str:
    """One rung up, or "" when unknown/already top; never raises."""
    try:
        i = rung_index(tier)
        if i < 0 or i + 1 >= len(RUNGS):
            return ""
        return RUNGS[i + 1]
    except Exception:  # noqa: BLE001 -- lookup never raises
        return ""


def tier_of(card) -> str:
    """Bloom tier for a queue card; "" when unknown. Never raises.

    Prefers an explicit ``tier`` key, else resolves ``exercise_type``
    through ``exercises.TYPES`` (the same table History uses).
    """
    try:
        if not isinstance(card, dict):
            return ""
        raw = card.get("tier")
        if isinstance(raw, str) and (
                raw.strip().lower() in RUNGS
                or raw.strip().lower() in _OFF_LADDER):
            return raw.strip().lower()
        try:
            etype = int(card.get("exercise_type"))
        except (TypeError, ValueError):
            return ""
        from . import exercises as exmod
        try:
            return str(exmod.TYPES[etype][1]).strip().lower()
        except (KeyError, IndexError, TypeError, AttributeError):
            return ""
    except Exception:  # noqa: BLE001 -- lookup never raises
        return ""


def normalize_grades(grades) -> list:
    """Oldest-first int grades clipped to 0..5; hostile input yields [].

    Floats are rounded, numeric strings parsed, anything else dropped.
    """
    try:
        if not isinstance(grades, (list, tuple)):
            return []
        out = []
        for g in grades:
            try:
                if isinstance(g, bool):
                    continue
                if isinstance(g, str):
                    g = float(g.strip())
                n = int(round(float(g)))
                out.append(max(0, min(5, n)))
            except (TypeError, ValueError):
                continue
        return out
    except Exception:  # noqa: BLE001 -- cleaning never raises
        return []


def pass_streak(grades, threshold: int = PASS_GRADE) -> int:
    """Trailing count of grades >= threshold; 0 on no data; never raises."""
    try:
        th = int(threshold)
    except (TypeError, ValueError):
        th = PASS_GRADE
    seq = normalize_grades(grades)
    n = 0
    for g in reversed(seq):
        if g >= th:
            n += 1
        else:
            break
    return n


def is_bored(grades, needed: int = STREAK_N,
             threshold: int = PASS_GRADE) -> bool:
    """True iff the trailing pass streak reaches `needed`.

    `needed` <= 1 means any single pass counts; hostile `needed`
    falls back to STREAK_N. Empty/hostile grade data is never bored
    (legacy fallback: queue order unchanged).
    """
    try:
        k = int(needed)
        if k < 1:
            k = 1
    except (TypeError, ValueError):
        k = STREAK_N
    try:
        return pass_streak(grades, threshold) >= k
    except Exception:  # noqa: BLE001 -- detection never raises
        return False


def suggest_rung(tier, grades, needed: int = STREAK_N) -> str:
    """Next rung up when bored, else the canonical tier key (or "" unknown).

    Legacy fallback: with no grade data, or when the tier is unknown or
    already the top rung, returns the canonical key unchanged
    ("" when unknown) so callers keep today's queue order.
    """
    try:
        key = _canon(tier)
        if key not in RUNGS:
            return ""
        if is_bored(grades, needed):
            return next_rung(key) or key
        return key
    except Exception:  # noqa: BLE001 -- suggestion never raises
        return ""


def promote(cards, grades_by_concept=None, needed: int = STREAK_N) -> list:
    """Due-queue order with bored concepts' hardest cards first.

    Pure reorder: stable, never drops or duplicates cards. Card tiers
    resolve via ``tier_of`` (explicit key, else exercise type). A
    concept is bored when its grade tail (oldest-first) hits the pass
    streak; histories mix tiers, so "up" means the concept's
    highest-tier queued cards lead, the rest of its cards follow, then
    every calm concept in input order. Empty/hostile input returns a
    same-order copy (legacy fallback).
    """
    try:
        if not isinstance(cards, list) or not cards:
            return list(cards) if isinstance(cards, list) else []
        hist = grades_by_concept if isinstance(grades_by_concept, dict) else {}
        bored: set = set()
        for c in cards:
            try:
                if not isinstance(c, dict):
                    continue
                cid = c.get("concept_id")
                if cid is None or cid in bored:
                    continue
                if is_bored(hist.get(cid), needed):
                    bored.add(cid)
            except Exception:  # noqa: BLE001 -- one bad card skips
                continue
        keyed = []
        for pos, card in enumerate(cards):
            try:
                if isinstance(card, dict) and card.get("concept_id") in bored:
                    ti = rung_index(tier_of(card))
                    sub = -ti if ti >= 0 else 1
                    keyed.append((0, sub, pos, card))
                else:
                    keyed.append((1, 0, pos, card))
            except Exception:  # noqa: BLE001 -- one bad card skips
                keyed.append((1, 0, pos, card))
        keyed.sort(key=lambda t: (t[0], t[1], t[2]))
        return [c for _, _, _, c in keyed]
    except Exception:  # noqa: BLE001 -- ordering never raises
        try:
            return list(cards)
        except TypeError:
            return []


def badge_html(tier, grades, needed: int = STREAK_N) -> str:
    """'Too easy — try <next>' badge when bored, else ""; never raises."""
    try:
        if not is_bored(grades, needed):
            return ""
        nxt = next_rung(tier)
        if not nxt:
            return ""
        return ("<span class='chip boredom'>Too easy \u2014 try "
                f"{htmlmod.escape(nxt)}</span>")
    except Exception:  # noqa: BLE001 -- renderers must never raise
        return ""


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {"id": "boredom-detection", "kind": "feature",
            "title": "Boredom detection",
            "blurb": "Acing reviews in a row jumps one Bloom rung up "
                     "instead of more same-level drills.",
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection with a live badge sample; db-free."""
    try:
        sample = badge_html("apply", [4, 5, 5])
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Boredom detection "
            "<small>(feature)</small></h3>"
            "<p>When the trailing pass streak (grades 4-5, oldest-first, "
            "current grade included) reaches three, the Due queue offers "
            "the next Bloom rung up for that concept: "
            "<code>groundwork/boredom.py</code> provides "
            "<code>is_bored()</code>/<code>suggest_rung()</code> (fail "
            "closed: no grade data means not bored, same tier) plus a pure "
            "<code>promote()</code> reorder and a "
            "<code>badge_html()</code> that is empty unless bored. A live "
            "sample renders below.</p>"
            f"{sample}"
        )
    except Exception:  # noqa: BLE001 -- status must always render
        return f"<h3 id='{STATUS_ANCHOR}'>Boredom detection</h3>"
