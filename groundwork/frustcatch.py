"""Frustration detection: three fast fails route to an easier card (F-96).

A learner who fails the same card three times in a row without a
pause is grinding, not learning: repeating the same hard card deepens
frustration while memory keeps slipping. This module spots that tail
pattern over recent review attempts and routes relief -- an easier card
on the same concept plus a short encouragement note.

Caller path (grading, never a Status demo): ``MCPServer.submit_review``
in groundwork/mcp.py grades each answer and reschedules the card; it
consults ``relief_plan`` over the card's grade history (including the
just-given grade) with sibling same-concept cards as the easier pool
and, when ``frustrated`` is True, returns a ``relief`` banner that the
result page renders under the verdict. With no attempt history every
helper returns its legacy value (not frustrated, no easier card, ""
markup), so calm learners see byte-identical feedback. No web.py logic
moves here, just the submit_review call, one banner line on the result
page, and no queue mutation.

An attempt is ``{"grade": 0-5, "seconds": float | None}``. A fast fail
is a grade at or below 2 given within 120 seconds -- or with no timing
at all, so legacy review rows without durations still count. Bare grade
ints are accepted as attempts with unknown timing. Never raises; hostile
input yields the legacy calm values.
"""
from __future__ import annotations

import html as htmlmod

STATUS_ANCHOR = "status-b21-frustcatch"

FAIL_CUTOFF = 2
FAST_SECONDS = 120.0
NEED_STREAK = 3


def normalize_attempts(attempts) -> list:
    """Cleaned [{grade, seconds}] list; hostile input yields []."""
    try:
        if not isinstance(attempts, (list, tuple)):
            return []
        out = []
        for att in attempts:
            if isinstance(att, (int, float)) and not isinstance(att, bool):
                out.append({"grade": int(att), "seconds": None})
            elif isinstance(att, dict):
                try:
                    grade = int(att.get("grade", 0))
                except (TypeError, ValueError):
                    continue
                secs = att.get("seconds", att.get("duration"))
                try:
                    secs = float(secs) if secs is not None else None
                except (TypeError, ValueError):
                    secs = None
                if secs is not None and secs < 0:
                    secs = None
                out.append({"grade": max(0, min(5, grade)),
                            "seconds": secs})
        return out
    except Exception:  # noqa: BLE001 -- normalizing never raises
        return []


def is_fast_fail(attempt, grade_cutoff: int = FAIL_CUTOFF,
                 max_seconds: float = FAST_SECONDS) -> bool:
    """True for one low grade given quickly; False on hostile input."""
    try:
        attempts = normalize_attempts([attempt])
        if not attempts:
            return False
        att = attempts[0]
        if att["grade"] > grade_cutoff:
            return False
        if att["seconds"] is None:
            return True
        return att["seconds"] <= max_seconds
    except Exception:  # noqa: BLE001 -- lookup never raises
        return False


def tail_streak(attempts, grade_cutoff: int = FAIL_CUTOFF,
                max_seconds: float = FAST_SECONDS) -> int:
    """Consecutive fast fails at the tail; 0 when none/hostile."""
    try:
        clean = normalize_attempts(attempts)
        streak = 0
        for att in reversed(clean):
            if att["grade"] > grade_cutoff:
                break
            if att["seconds"] is not None and att["seconds"] > max_seconds:
                break
            streak += 1
        return streak
    except Exception:  # noqa: BLE001 -- counting never raises
        return 0


def is_frustrated(attempts, need: int = NEED_STREAK) -> bool:
    """True once the tail holds `need` fast fails; False otherwise."""
    try:
        need = max(1, int(need))
    except (TypeError, ValueError):
        need = NEED_STREAK
    try:
        return tail_streak(attempts) >= need
    except Exception:  # noqa: BLE001 -- check never raises
        return False


def encouragement(streak: int = NEED_STREAK) -> str:
    """Short supportive note; never raises, never empty."""
    try:
        n = int(streak)
    except (TypeError, ValueError):
        n = NEED_STREAK
    try:
        if n <= 1:
            return ("That one slipped -- normal. Take a breath and "
                    "try the next card fresh.")
        return (f"{max(n, 0)} misses in a row is a signal, not a verdict: "
                "your brain is asking for a smaller step. Take an easier "
                "card below and rebuild -- the hard one will wait.")
    except Exception:  # noqa: BLE001 -- note never raises
        return "Take a breath and try a smaller step."


def easier_card(cards, current_id=None):
    """Easiest card dict not equal to current; None when none usable.

    Cards carry ``id`` plus optional ``difficulty`` (0-1, lower is
    easier) or ``stability`` (lower is fresher). Legacy no-data fallback:
    empty/hostile input yields None so the queue order is unchanged.
    """
    try:
        if not isinstance(cards, (list, tuple)) or not cards:
            return None
        pool = [c for c in cards
                if isinstance(c, dict) and c.get("id") != current_id]
        if not pool:
            return None

        def _ease(card) -> float:
            try:
                return float(card.get("difficulty", 0.5))
            except (TypeError, ValueError):
                return 0.5

        return min(pool, key=_ease)
    except Exception:  # noqa: BLE001 -- picking never raises
        return None


def relief_plan(attempts, cards=None, current_id=None) -> dict:
    """One relief decision: {frustrated, streak, easier, message}.

    Calm histories (and all hostile input) yield the legacy value:
    ``{"frustrated": False, "streak": 0, "easier": None, "message": ""}``
    so grading renders byte-identical feedback when no relief applies.
    """
    try:
        streak = tail_streak(attempts)
        if streak < NEED_STREAK:
            return {"frustrated": False, "streak": streak,
                    "easier": None, "message": ""}
        easy = easier_card(cards, current_id)
        return {"frustrated": True, "streak": streak,
                "easier": easy, "message": encouragement(streak)}
    except Exception:  # noqa: BLE001 -- planning never raises
        return {"frustrated": False, "streak": 0,
                "easier": None, "message": ""}


def banner_html(plan, lesson_url: str = "") -> str:
    """Relief banner for the grading feedback; "" when calm/hostile.

    Empty plans return "" so pass/fail feedback without frustration
    renders byte-identical (legacy no-data fallback). The easier-card
    link renders only when a real lesson URL is supplied — never a
    dead link. Never raises.
    """
    try:
        if not isinstance(plan, dict) or not plan.get("frustrated"):
            return ""
        msg = htmlmod.escape(str(plan.get("message", "")))
        easy = plan.get("easier")
        link = ""
        if (isinstance(easy, dict) and easy.get("id")
                and isinstance(lesson_url, str) and lesson_url):
            url = htmlmod.escape(lesson_url, quote=True)
            link = (f" <a href='{url}'>Try an easier card "
                    f"instead</a>")
        return f"<p class='relief'>{msg}.{link}</p>"
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        sample = banner_html(relief_plan(
            [{"grade": 1}, {"grade": 0}, {"grade": 2}],
            [{"id": "easy-1", "difficulty": 0.2}], "hard-9"))
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Frustration relief "
            "<small>(feature)</small></h3>"
            "<p>Three fast fails in a row route you to an easier card "
            "plus a breather note -- <code>groundwork/frustcatch.py</code> "
            "watches the grading path (<code>MCPServer.submit_review</code>) "
            "and only speaks up at the third straight miss; calm reviews "
            "render exactly as before.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Frustration relief</h3>"
                "<p>Relief help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "frustration-relief",
        "kind": "feature",
        "title": "Stuck? Take the easier card",
        "blurb": ("Three fast fails in a row earn a breather note and "
                  "an easier card on the same idea."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
