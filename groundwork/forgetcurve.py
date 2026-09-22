"""Forgetting-curve personalization (F-91): reviews timed to your decay.

A personal decay constant ``k`` multiplies forgetting speed in the
FSRS-lite formula ``R=(1+t/9(S/k))^-1``. ``fit_decay`` estimates ``k``
from recall history (worse-than-expected recall pushes ``k`` up,
better pushes it down; no data stays 1.0, the legacy curve exactly).
The Due queue uses it twice: ``minisession.apply_dial`` floors on the
personal curve, and ``order_due`` ranks most-forgotten first. Stdlib
only (``math``); no I/O, never raises.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b20-forgetcurve"

K_MIN = 0.4
K_MAX = 2.5
PASS_GRADE = 3


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clean_attempts(rows) -> list:
    """[(stability, lag_days, recalled)] recall events; [] when none.

    Rows are mappings (or tuples) of card_id, stability, grade,
    reviewed_at. Lags run between consecutive reviews of one card, so
    each card's first review contributes no event. Never raises.
    """
    try:
        by_card: dict = {}
        for row in rows or []:
            try:
                if isinstance(row, dict):
                    cid = row.get("card_id", "")
                    stab, grade, when = (row.get("stability"),
                                         row.get("grade"),
                                         row.get("reviewed_at"))
                else:
                    cid, stab, grade, when = row[0], row[1], row[2], row[3]
            except (TypeError, IndexError, KeyError):
                continue
            stab, grade = _num(stab), _num(grade)
            when = str(when or "")
            if not cid or stab is None or grade is None or not when:
                continue
            by_card.setdefault(str(cid), []).append((stab, when, grade))
        events = []
        for attempts in by_card.values():
            attempts.sort(key=lambda a: a[1])
            for (prev_s, prev_when, _), (stab, when, grade) in zip(
                    attempts, attempts[1:]):
                try:
                    from datetime import date
                    lag = (date.fromisoformat(when[:10])
                           - date.fromisoformat(prev_when[:10])).days
                except Exception:  # noqa: BLE001 -- bad stamp, skip event
                    continue
                if lag < 0:
                    continue
                _ = prev_s
                events.append((stab, float(lag), grade >= PASS_GRADE))
        return events
    except Exception:  # noqa: BLE001
        return []


def _expected(stability, lag) -> float | None:
    try:
        from . import sched as schedmod
        return schedmod.retrievability(float(stability), float(lag))
    except Exception:  # noqa: BLE001
        return None


def fit_decay(events) -> float:
    """Personal decay in [0.4, 2.5]; 1.0 with no usable data."""
    try:
        usable = []
        for ev in events or []:
            try:
                stab, lag, ok = float(ev[0]), float(ev[1]), bool(ev[2])
            except (TypeError, IndexError, ValueError):
                continue
            exp = _expected(stab, lag)
            if exp is None:
                continue
            usable.append((exp, ok))
        if not usable:
            return 1.0
        expected = sum(e for e, _ in usable) / len(usable)
        if expected >= 1.0:
            return 1.0
        observed = sum(1.0 if ok else 0.0 for _, ok in usable) / len(usable)
        return max(K_MIN, min(K_MAX, (1.0 - observed) / (1.0 - expected)))
    except Exception:  # noqa: BLE001 -- fitting never raises
        return 1.0


def effective_stability(stability, k) -> float:
    """Stability under decay k (S/k); S back on hostile input."""
    try:
        stab = float(stability)
        kk = float(k)
        if kk <= 0:
            return stab
        return stab / kk
    except (TypeError, ValueError):
        try:
            return float(stability)
        except (TypeError, ValueError):
            return 0.0


def personal_retrievability(stability, elapsed_days, k=None) -> float:
    """Recall probability under decay k; legacy curve exactly at None."""
    try:
        if k is None:
            from . import sched as schedmod
            return schedmod.retrievability(stability, elapsed_days)
        stab = float(stability)
        if stab <= 0:
            return 0.0
        kk = float(k)
        if kk <= 0:
            kk = 1.0
        return (1.0 + float(elapsed_days) / (9.0 * (stab / kk))) ** -1
    except (TypeError, ValueError):
        try:
            from . import sched as schedmod
            return schedmod.retrievability(stability, elapsed_days)
        except Exception:  # noqa: BLE001
            return 0.0


def overdue_days(card, now: str = "") -> float:
    """Days past the card's due date (floor 0); 0.0 on hostile input."""
    try:
        due = (card or {}).get("due", "")
        if not isinstance(due, str) or not due.strip():
            return 0.0
        from datetime import date, datetime, timezone
        end = (date.fromisoformat(now[:10]) if isinstance(now, str) and now.strip()
               else datetime.now(timezone.utc).date())
        return max(0.0, (end - date.fromisoformat(due.strip()[:10])).days)
    except Exception:  # noqa: BLE001
        return 0.0


def _card_k(card, decays) -> float | None:
    try:
        if isinstance(decays, dict):
            cid = (card or {}).get("id", "")
            got = decays.get(cid, decays.get(str(cid), None))
            return float(got) if got is not None else None
        return float(decays)
    except (TypeError, ValueError, AttributeError):
        return None


def order_due(cards, decays=None, now: str = "") -> list:
    """Most-forgotten first under personal decays; input back by default.

    ``decays`` is a global k or {card_id: k}. No decays, or every k at
    1.0, returns the input order untouched — the legacy default. Stable
    sort, never mutates input, never raises.
    """
    try:
        items = [c for c in (cards or []) if isinstance(c, dict)]
        if not items:
            return []
        if decays is None:
            return list(items)
        if isinstance(decays, dict) and not decays:
            return list(items)
        keys = []
        personalized = False
        for c in items:
            k = _card_k(c, decays)
            if k is not None and k != 1.0:
                personalized = True
            stab = _num(c.get("stability", 1.0))
            keys.append(personal_retrievability(
                stab if stab is not None else 1.0,
                overdue_days(c, now), k))
        if not personalized:
            return list(items)
        return [c for _, c in sorted(zip(keys, items), key=lambda kv: kv[0])]
    except Exception:  # noqa: BLE001
        try:
            return list(cards or [])
        except Exception:  # noqa: BLE001
            return []


def describe(k) -> str:
    """One-line decay verdict; never raises."""
    try:
        kk = float(k)
        if kk > 1.15:
            return (f"Fast fader (k={kk:.2f}) — reviews return sooner.")
        if kk < 0.87:
            return (f"Slow fader (k={kk:.2f}) — reviews return later.")
        return f"Steady curve (k={kk:.2f}) — the standard schedule fits."
    except (TypeError, ValueError):
        return "Steady curve — the standard schedule fits."


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    sample = (f"<p>{describe(1.6)}</p><p>{describe(0.7)}</p>")
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Your forgetting curve <small>(feature)</small></h3>"
        "<p>Reviews timed to your decay — fast faders return sooner, "
        "slow faders later. <code>groundwork/forgetcurve.py</code> fits "
        "your decay constant from recall history and the Due queue "
        "floors and orders on your curve "
        "(<code>minisession.apply_dial</code>); with no history the "
        "standard schedule stands. Live samples render below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "forgetting-curve",
        "kind": "feature",
        "title": "Your forgetting curve",
        "blurb": "Reviews timed to your decay — fast faders return "
                 "sooner, slow faders later.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
