"""Confidence-weighted scoring (F-65): brave-correct beats shy-correct.

Grades today are pass/fail — a hesitant correct and a certain
correct score the same, so calibration never pays. This module owns
the honesty premium: a correct answer earns its confidence (1–5
points), a wrong one loses its confidence (−5..−1). The order is the
contract: brave-correct (5) > shy-correct (1) > shy-wrong (−1) >
brave-wrong (−5). Confidence clamps to 1–5, non-answers score
nothing. Db-free library — grading is untouched; pure functions,
stdlib only, no I/O, no DB changes.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b13-confweight"

CONF_MIN = 1
CONF_MAX = 5


def clamp_conf(conf) -> int:
    """Confidence clamped to 1–5; garbage fails closed to 3."""
    try:
        return min(CONF_MAX, max(CONF_MIN, int(conf)))
    except Exception:  # noqa: BLE001 -- scoring must never raise
        return 3


def score(correct, conf) -> int:
    """Signed points: +confidence when right, −confidence when wrong.

    ``correct`` accepts True/False (truthy pass grades count as
    True); anything unparseable scores 0 — a missing answer is not a
    shy wrong.
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
        bound = clamp_conf(conf)
        return bound if value else -bound
    except Exception:  # noqa: BLE001 -- scoring must never raise
        return 0


def rank_line(conf) -> str:
    """One-line table stake: what this confidence risks and wins."""
    try:
        bound = clamp_conf(conf)
        return (f"confidence {bound}: right earns +{bound}, "
                f"wrong costs −{bound}")
    except Exception:  # noqa: BLE001 -- display must never raise
        return "confidence 3: right earns +3, wrong costs −3"


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    rows = "".join(
        f"<tr><td>{label}</td><td>{pts:+d}</td></tr>"
        for label, pts in (
            ("brave-correct (5)", score(True, 5)),
            ("shy-correct (1)", score(True, 1)),
            ("shy-wrong (1)", score(False, 1)),
            ("brave-wrong (5)", score(False, 5))))
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Confidence-weighted scoring <small>(feature)</small></h3>"
        "<p>Calibration now pays: <code>groundwork/confweight.py</code> "
        "provides <code>score()</code> (right earns its confidence, "
        "wrong loses it — brave-correct beats shy-correct beats "
        "shy-wrong beats brave-wrong) and <code>rank_line()</code>, a "
        "db-free library that leaves grading untouched. The table "
        "below is computed live, not typed.</p>"
        "<table class='log'><tr><th>Answer</th><th>Points</th></tr>"
        f"{rows}</table>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "conf-scoring",
        "kind": "feature",
        "title": "Confidence-weighted scoring",
        "blurb": "Brave-correct beats shy-correct — calibration pays, overconfidence costs.",
        "path": "/status",
        "anchor": "status-b13-confweight",
    }
