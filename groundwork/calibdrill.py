"""Calibration training drills (F-66): bet points on answers, explicit odds.

Learners state confidence but never feel its price — 90% sure and
wrong costs the same shrug as 60% sure and wrong. Drills put points
behind the number: a stated confidence sets explicit odds, and the
settle pays or charges accordingly. The odds are fair: at the honest
probability the expected value is exactly zero, so only genuine
calibration (not bravado, not modesty) earns points over time.

``offer`` maps confidence 1–5 to an implied probability and a
win/lose pair (stake 10, scaled by the honest miss); ``settle``
pays it out; ``drill_html`` renders the drill card. Db-free library
— grading and reviews are untouched; pure functions, stdlib only
(``html``), no I/O, no DB changes.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b13-calibdrill"

CONF_MIN = 1
CONF_MAX = 5
STAKE = 10


def clamp_conf(conf) -> int:
    """Confidence clamped to 1–5; garbage fails closed to 3."""
    try:
        return min(CONF_MAX, max(CONF_MIN, int(conf)))
    except Exception:  # noqa: BLE001 -- drill must never raise
        return 3


def implied_p(conf) -> float:
    """Honest probability behind a stated confidence (conf/5)."""
    return clamp_conf(conf) / 5.0


def offer(conf) -> dict:
    """Explicit odds for a stated confidence: win, lose, and p.

    ``win = round(STAKE * (1 - p))``, ``lose = -round(STAKE * p)``:
    at the honest probability the expected value is ~0 (within a
    point of rounding), so only calibration earns over time.
    """
    try:
        p = implied_p(conf)
        return {"confidence": clamp_conf(conf), "p": round(p, 2),
                "win": round(STAKE * (1 - p)),
                "lose": -round(STAKE * p)}
    except Exception:  # noqa: BLE001 -- drill must never raise
        return {"confidence": 3, "p": 0.6, "win": 4, "lose": -6}


def settle(conf, correct) -> int:
    """Points won (+) or lost (−) for a drilled answer.

    Unparseable correctness settles nothing (0) — a missing answer
    is not a lost bet.
    """
    try:
        if correct is None:
            return 0
        if isinstance(correct, str):
            text = correct.strip().lower()
            if text in ("", "none", "null", "error"):
                return 0
            value = text not in ("0", "false", "no", "fail", "wrong")
        else:
            value = bool(correct)
        deal = offer(conf)
        return deal["win"] if value else deal["lose"]
    except Exception:  # noqa: BLE001 -- drill must never raise
        return 0


def drill_html(prompt: str = "", conf: int = 3) -> str:
    """Drill card: the question, the odds, the stake. All escaped."""
    try:
        deal = offer(conf)
        safe = html.escape((prompt or "State the invariant.").strip()
                           or "State the invariant.")
        return (
            "<article class='calib-drill'>"
            f"<p class='drill-q'>{safe}</p>"
            f"<p>Confidence {deal['confidence']} means "
            f"{int(deal['p'] * 100)}% — right wins "
            f"<b>+{deal['win']}</b>, wrong loses "
            f"<b>{deal['lose']}</b>. Bet only what you believe.</p>"
            "</article>")
    except Exception:  # noqa: BLE001 -- drill must never raise
        return "<article class='calib-drill'></article>"


def section_html() -> str:
    """Status-page subsection with a live drill card."""
    demo = drill_html("This retry loop terminates on success.", 4)
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Calibration drills <small>(feature)</small></h3>"
        "<p>Confidence now has a price: "
        "<code>groundwork/calibdrill.py</code> provides "
        "<code>offer()</code> (explicit win/lose odds per confidence, "
        "fair at the honest probability), <code>settle()</code>, and "
        "<code>drill_html()</code>. Since Batch 15 the odds ride every "
        "confidence widget and each verdict settles the stated bet — "
        "the banked currency stays the review score, shown beside it. "
        "Bet only what you believe — a live drill renders below.</p>" + demo)


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "calib-drills",
        "kind": "feature",
        "title": "Calibration drills",
        "blurb": "Bet points on answers at explicit odds — fair when honest, profitable only when calibrated.",
        "path": "/status",
        "anchor": "status-b13-calibdrill",
    }
