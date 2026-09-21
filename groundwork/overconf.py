"""Overconfidence interventions (F-67): extra evidence when the gap is large.

The calibration coach *shows* the accuracy-vs-confidence gap, then
leaves the learner alone with it. Chronically overconfident learners
need a nudge, not a number: when mean confidence outruns accuracy by
GAP_TRIGGER (0.25) over at least MIN_ATTEMPTS (10) attempts, this
module deals an intervention card — the gap stated plainly, the
weakest skill named, and one concrete counter-habit (a drill, a
dial-down, a re-read). Below the attempt floor, or when confidence
trails accuracy (underconfidence is not this card's problem), no
card: silence, not noise. Db-free library — reviews and the coach
are untouched; pure functions, stdlib only (``html``), no I/O, no
DB changes.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b13-overconf"

#: Confidence-minus-accuracy gap that deals the card.
GAP_TRIGGER = 0.25
#: Attempts before any gap counts (small samples lie).
MIN_ATTEMPTS = 10


def gap(accuracy, mean_conf) -> float:
    """Mean-confidence/5 minus accuracy; garbage fails closed to 0."""
    try:
        acc = float(accuracy)
        conf = float(mean_conf) / 5.0
        if acc != acc or conf != conf:  # NaN never intervenes
            return 0.0
        return conf - acc
    except Exception:  # noqa: BLE001 -- card must never raise
        return 0.0


def needs_intervention(gap_value, attempts: int = 0,
                       skill: str = "") -> bool:
    """True only for a large gap over enough attempts.

    ``skill`` is accepted so callers can pass their weakest skill in
    one call, but it never affects the verdict — the numbers decide.
    """
    try:
        try:
            g = float(gap_value)
        except Exception:  # noqa: BLE001 -- verdict must never raise
            return False
        try:
            n = int(attempts)
        except Exception:  # noqa: BLE001 -- verdict must never raise
            return False
        return g >= GAP_TRIGGER and n >= MIN_ATTEMPTS
    except Exception:  # noqa: BLE001 -- verdict must never raise
        return False


def intervention_html(gap_value, skill: str = "",
                      attempts: int = 0) -> str:
    """The card: gap stated, weakest skill named, one counter-habit.

    Renders empty unless ``needs_intervention`` fires — callers can
    emit unconditionally and the card stays silent on its own.
    """
    try:
        if not needs_intervention(gap_value, attempts, skill):
            return ""
        g = float(gap_value)
        name = html.escape((skill or "this skill").strip()
                           or "this skill")
        points = max(0, min(100, int(round(g * 100))))
        return (
            "<article class='overconf-card'>"
            "<p><b>Overconfidence check:</b> your confidence outruns "
            f"your accuracy by {points} points.</p>"
            f"<p>Weakest spot: {name}. Counter-habit for the next "
            "session: drop one confidence point on every answer there "
            "— bet only what past you actually earned.</p>"
            "</article>")
    except Exception:  # noqa: BLE001 -- card must never raise
        return ""


def coach_card(rows) -> str:
    """Live intervention card over real attempts (Batch 15, F-67).

    ``rows`` are (skill label, grade 0–5, confidence 1–5) — the same
    attempts the calibration coach reads. Fires only at MIN_ATTEMPTS+
    attempts with gap >= GAP_TRIGGER; the weakest skill is the
    largest per-skill confidence-minus-accuracy gap. Accuracy here is
    mean grade / 5 (the card states its own numbers, same scale as
    gap()). Unparseable rows are skipped; never raises.
    """
    try:
        items = []
        for row in rows or []:
            try:
                skill, grade, conf = row
                g = float(grade)
                c = float(conf)
                if g != g or c != c:  # NaN never intervenes
                    continue
                label = str(skill or "this skill").strip() or "this skill"
                items.append((label, g, c))
            except Exception:  # noqa: BLE001 -- bad row, skip it
                continue
        n = len(items)
        if n < MIN_ATTEMPTS:
            return ""
        acc = sum(g for _, g, _ in items) / n / 5.0
        mean_conf = sum(c for _, _, c in items) / n
        g = gap(acc, mean_conf)
        if not needs_intervention(g, n):
            return ""
        by_skill: dict = {}
        for label, grade, conf in items:
            by_skill.setdefault(label, []).append((grade, conf))
        worst_label, worst_gap = "this skill", None
        for label, rs in by_skill.items():
            cell = sum(c for _, c in rs) / len(rs) / 5.0 - sum(
                gr for gr, _ in rs) / len(rs) / 5.0
            if worst_gap is None or cell > worst_gap:
                worst_label, worst_gap = label, cell
        return intervention_html(g, worst_label, n)
    except Exception:  # noqa: BLE001 -- card must never raise
        return ""


def section_html() -> str:
    """Status-page subsection with a live dealt card."""
    demo = intervention_html(0.34, "cache invalidation", 24)
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Overconfidence cards <small>(feature)</small></h3>"
        "<p>Big calibration gaps now deal a card, not just a number: "
        "<code>groundwork/overconf.py</code> provides "
        "<code>gap()</code>, <code>needs_intervention()</code> (gap "
        "≥ 0.25 over ≥ 10 attempts — small samples and "
        "underconfidence stay silent), and "
        "<code>intervention_html()</code>. Since Batch 15 the History "
        "coach deals <code>coach_card()</code> from live attempts, "
        "naming the real weakest skill. A dealt card for a 34-point "
        "gap renders below.</p>" + demo)


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "overconf-cards",
        "kind": "feature",
        "title": "Overconfidence cards",
        "blurb": "Confidence outrunning accuracy by 25 points deals an intervention card with one counter-habit.",
        "path": "/status",
        "anchor": "status-b13-overconf",
    }
