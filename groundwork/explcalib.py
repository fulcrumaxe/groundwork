"""Calibration-aware explainer levels (I-122): auto-place from mastery + recency.

``render_levels`` auto-places from mastery alone; learners who grade
themselves confidently while failing (overconfident) get simpler
words, and accurate-but-shy learners get a rung up. With no recent
(grade, confidence) rows the legacy ``explain.auto_level`` value is
returned unchanged. Stdlib only; no I/O, never raises.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b20-explcalib"

TAIL = 5
OVER_GAP = 0.20
UNDER_GAP = -0.20
HIGH_ACC = 0.80


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def recent_gap(recent) -> float | None:
    """Mean confidence minus mean grade (both /5) over the last 5 rows.

    Positive means overconfident, negative underconfident; None when
    no usable row exists. Never raises.
    """
    try:
        if not recent:
            return None
        usable = []
        for row in recent:
            try:
                grade, conf = row[0], row[1]
            except (TypeError, IndexError, KeyError):
                continue
            grade, conf = _num(grade), _num(conf)
            if grade is None or conf is None:
                continue
            usable.append((grade / 5.0, conf / 5.0))
        tail = usable[-TAIL:]
        if not tail:
            return None
        return (sum(c for _, c in tail) / len(tail)
                - sum(g for g, _ in tail) / len(tail))
    except Exception:  # noqa: BLE001
        return None


def recent_from_rows(rows, newest_first: bool = True) -> list:
    """(grade, confidence) pairs, oldest-first; [] on hostile input.

    Accepts mappings with ``grade``/``confidence`` keys (review rows)
    or plain (grade, confidence) pairs. Newest-first input (the
    history-query order) is reversed so ``recent_gap`` tails the most
    recent five; mappings carrying ``reviewed_at`` are resorted
    newest-first first, so merged multi-card histories stay ordered.
    Never raises.
    """
    try:
        items = list(rows or [])
    except TypeError:
        return []
    try:
        def _when(row):
            try:
                got = (row.get("reviewed_at") if isinstance(row, dict)
                       else row["reviewed_at"])
            except (TypeError, KeyError, IndexError):
                got = None
            return got or ""

        if any(_when(r) for r in items):
            items.sort(key=_when, reverse=True)
            newest_first = True
    except Exception:  # noqa: BLE001 -- ordering is best-effort
        pass
    try:
        pairs = []
        for row in items:
            grade = conf = None
            try:
                if isinstance(row, dict):
                    grade, conf = row.get("grade"), row.get("confidence")
                else:
                    try:
                        grade, conf = row["grade"], row["confidence"]
                    except (TypeError, KeyError, IndexError):
                        grade, conf = row[0], row[1]
            except (TypeError, IndexError, KeyError):
                continue
            grade, conf = _num(grade), _num(conf)
            if grade is None or conf is None:
                continue
            pairs.append((grade, conf))
        if newest_first:
            pairs.reverse()
        return pairs
    except Exception:  # noqa: BLE001
        return []


def recent_accuracy(recent) -> float | None:
    """Mean grade (/5) over the last 5 usable rows; None when empty."""
    try:
        if not recent:
            return None
        grades = []
        for row in recent:
            try:
                grade = _num(row[0])
            except (TypeError, IndexError, KeyError):
                continue
            if grade is not None:
                grades.append(grade / 5.0)
        tail = grades[-TAIL:]
        if not tail:
            return None
        return sum(tail) / len(tail)
    except Exception:  # noqa: BLE001
        return None


def pick_level(mastery, n_reviews, recent=None) -> int:
    """Auto level with a calibration nudge; legacy value without data."""
    try:
        from . import explain as explainmod
        try:
            base = explainmod.auto_level(float(mastery or 0.0),
                                         int(n_reviews or 0))
        except (TypeError, ValueError):
            base = 2
        gap = recent_gap(recent)
        if gap is None:
            return base
        if gap >= OVER_GAP:
            return max(1, base - 1)
        acc = recent_accuracy(recent)
        if gap <= UNDER_GAP and acc is not None and acc >= HIGH_ACC:
            return min(4, base + 1)
        return base
    except Exception:  # noqa: BLE001 -- placement never raises
        try:
            from . import explain as explainmod
            return explainmod.auto_level(0.0, 0)
        except Exception:  # noqa: BLE001
            return 2


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    sample = (f"<p>Overconfident streaks step one rung down; accurate "
              f"but shy streaks step one up. Gap window: last {TAIL} "
              f"reviews; thresholds {OVER_GAP:+.2f}/{UNDER_GAP:+.2f}.</p>")
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Levels that read your calibration <small>(improvement)</small></h3>"
        "<p>Auto-level now weighs recent calibration, not just mastery. "
        "<code>groundwork/explcalib.py</code> compares mean confidence "
        "against mean grade on the lesson rendering path "
        "(<code>lessons.render_levels</code>); with no recent reviews "
        "the legacy placement stands.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "calibration-levels",
        "kind": "improvement",
        "title": "Levels that read your calibration",
        "blurb": "Auto-level now weighs recent calibration, not just mastery.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
