"""Flow detection (F-95): extend sessions when accuracy plus pace are high.

A learner answering fast *and* well is in flow — cutting the session
off on schedule wastes momentum, while stretching every session burns
tired learners out. This module owns the gate: over the recent attempt
window it checks accuracy (share of grades >= 4) plus pace (median
seconds per card) and says whether the Due session may grow by a few
bonus cards.

Pace comes from ``reviewed_at`` deltas between consecutive reviews
(``attempts_with_pace``); the reviews table carries no per-attempt
timer, so a gap over 10 minutes counts as a session break with no
pace evidence rather than a slow answer.

Db-free library — pure functions, stdlib only, no I/O, no DB changes.
Thin delegation from the caller::

    picks = flowdetect.extend_session(picks, due, attempts)

Caller path (real learner path, never a Status demo):
``minisession.session_box_html`` extends its budgeted picks when the
Due page supplies recent attempts (``flow_attempts``); the Due page
builds them from the last reviews via ``attempts_with_pace``. No
attempts means no extension — the planned session stands.

Legacy no-data fallback: empty or unreadable attempts never count as
flow, so ``extend_session`` returns the planned picks unchanged.
"""

from __future__ import annotations

from datetime import datetime, timezone

STATUS_ANCHOR = "status-b21-flowdetect"

MIN_RECENT = 3
WINDOW = 5
PASS_GRADE = 4
ACC_THRESHOLD = 0.8
PACE_CAP_S = 45.0
MAX_BONUS = 3
#: A gap this long (seconds) is a session break, not a slow answer.
GAP_CAP_S = 600.0
FLOW_ROWS = 6


def _parse_ts(value):
    """ISO reviewed_at -> aware UTC datetime; None when unparseable."""
    try:
        if not isinstance(value, str) or not value.strip():
            return None
        text = value.strip()
        try:
            dt = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            dt = datetime.fromisoformat(text)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
    except Exception:  # noqa: BLE001 -- parsing never raises
        return None


def attempts_with_pace(rows) -> list:
    """Newest-first ``{grade, reviewed_at}`` rows -> oldest-first attempts.

    Each attempt is ``{"grade": int}`` plus ``"secs"`` (seconds since
    the previous review) when both timestamps parse and the gap looks
    like answering pace (0..GAP_CAP_S). Session breaks and unparseable
    timestamps keep the grade but contribute no timing. Hostile input
    yields ``[]``; never raises.
    """
    try:
        items = list(rows or [])
        if not items:
            return []
        items = items[:FLOW_ROWS]
        parsed = []
        for r in items:
            try:
                if not isinstance(r, dict):
                    continue
                grade = int(r.get("grade"))
                if grade < 0 or grade > 5:
                    continue
                parsed.append({"grade": grade,
                               "at": _parse_ts(r.get("reviewed_at"))})
            except (TypeError, ValueError, AttributeError):
                continue
        parsed.reverse()  # oldest first
        out = []
        prev = None
        for row in parsed:
            att = {"grade": row["grade"]}
            if row["at"] is not None and prev is not None:
                gap = (row["at"] - prev).total_seconds()
                if 0 <= gap <= GAP_CAP_S:
                    att["secs"] = gap
            out.append(att)
            if row["at"] is not None:
                prev = row["at"]
        return out
    except Exception:  # noqa: BLE001 -- gate must never raise
        return []


def clean_attempts(attempts, window: int = WINDOW) -> list[dict]:
    """Usable recent attempts, oldest-first, capped to ``window``.

    Each attempt is a mapping with ``grade`` (0-5) and ``secs``
    (seconds spent). Entries missing a parseable grade are dropped;
    ``secs`` survives only when it parses to a non-negative number.
    Hostile input yields ``[]``; never raises.
    """
    try:
        try:
            n = max(1, int(window))
        except (TypeError, ValueError):
            n = WINDOW
        rows: list[dict] = []
        for a in attempts or []:
            try:
                if not isinstance(a, dict):
                    continue
                grade = int(a.get("grade"))
                if grade < 0 or grade > 5:
                    continue
                row: dict = {"grade": grade}
                try:
                    secs = float(a.get("secs"))
                    if secs == secs and secs >= 0:
                        row["secs"] = secs
                except (TypeError, ValueError):
                    pass
                rows.append(row)
            except (TypeError, ValueError, AttributeError):
                continue
        return rows[-n:]
    except Exception:  # noqa: BLE001 -- gate must never raise
        return []


def accuracy(recent) -> float:
    """Share of recent attempts graded >= 4; empty maps to 0.0."""
    try:
        rows = list(recent or [])
        if not rows:
            return 0.0
        good = sum(1 for r in rows
                   if isinstance(r, dict) and r.get("grade", 0) >= PASS_GRADE)
        return good / len(rows)
    except Exception:  # noqa: BLE001 -- gate must never raise
        return 0.0


def median_pace(recent) -> float | None:
    """Median seconds per card, or None when no timing is recorded."""
    try:
        secs = sorted(float(r["secs"]) for r in (recent or [])
                      if isinstance(r, dict) and "secs" in r)
        if not secs:
            return None
        mid = len(secs) // 2
        if len(secs) % 2:
            return secs[mid]
        return (secs[mid - 1] + secs[mid]) / 2.0
    except Exception:  # noqa: BLE001 -- gate must never raise
        return None


def in_flow(attempts, window: int = WINDOW,
            acc_threshold: float = ACC_THRESHOLD,
            pace_cap: float = PACE_CAP_S) -> bool:
    """True when the recent window shows high accuracy plus brisk pace.

    Needs at least MIN_RECENT graded attempts, accuracy >= threshold,
    and a recorded median pace within the cap. Missing timings fail
    closed (no flow); never raises.
    """
    try:
        try:
            need = float(acc_threshold)
        except (TypeError, ValueError):
            need = ACC_THRESHOLD
        try:
            cap = float(pace_cap)
        except (TypeError, ValueError):
            cap = PACE_CAP_S
        recent = clean_attempts(attempts, window)
        if len(recent) < MIN_RECENT:
            return False
        if accuracy(recent) < need:
            return False
        pace = median_pace(recent)
        if pace is None:
            return False
        return pace <= cap
    except Exception:  # noqa: BLE001 -- gate must never raise
        return False


def bonus_count(attempts, window: int = WINDOW,
                max_bonus: int = MAX_BONUS) -> int:
    """Bonus cards earned: MAX_BONUS scaled by accuracy, else 0.

    In flow, accuracy 0.8 earns 2 and a perfect window earns 3;
    out of flow (or garbage input) earns 0. Never raises.
    """
    try:
        try:
            cap = max(0, int(max_bonus))
        except (TypeError, ValueError):
            cap = MAX_BONUS
        recent = clean_attempts(attempts, window)
        if not in_flow(recent, window):
            return 0
        acc = accuracy(recent)
        return max(1, min(cap, int(round(acc * cap))))
    except Exception:  # noqa: BLE001 -- gate must never raise
        return 0


def extend_session(picks, due, attempts, window: int = WINDOW,
                   max_bonus: int = MAX_BONUS) -> list:
    """Planned picks plus up to ``bonus_count`` next-most-overdue cards.

    Bonus cards come from ``due`` in order, skipping ids already in
    ``picks``. Out of flow (or any bad input) the picks return as a
    new list, unchanged in content — the legacy no-data fallback.
    Never mutates its inputs; never raises.
    """
    try:
        base = [c for c in (picks or []) if isinstance(c, dict)]
        if not in_flow(attempts, window):
            return list(base)
        try:
            cap = max(0, int(max_bonus))
        except (TypeError, ValueError):
            cap = MAX_BONUS
        want = min(cap, bonus_count(attempts, window, cap))
        if want <= 0:
            return list(base)
        seen = {str(c.get("id", "")) for c in base}
        out = list(base)
        for c in (due or []):
            if len(out) >= len(base) + want:
                break
            if not isinstance(c, dict):
                continue
            if str(c.get("id", "")) not in seen:
                out.append(c)
                seen.add(str(c.get("id", "")))
        return out
    except Exception:  # noqa: BLE001 -- extension must never break Due
        try:
            return list(picks or [])
        except Exception:  # noqa: BLE001 -- last resort
            return []


def describe(attempts, window: int = WINDOW) -> str:
    """One-line reading of the flow gate for the Due page."""
    try:
        recent = clean_attempts(attempts, window)
        if len(recent) < MIN_RECENT:
            return "too early to tell — answer a few cards first"
        acc = accuracy(recent)
        pace = median_pace(recent)
        if pace is None:
            return f"accuracy {acc:.0%} but no timing yet — no extension"
        if in_flow(recent, window):
            return (f"in flow — accuracy {acc:.0%}, "
                    f"median {pace:.0f}s/card: session may grow")
        if acc < ACC_THRESHOLD:
            return (f"accuracy {acc:.0%} below "
                    f"{ACC_THRESHOLD:.0%} — steady pace, no extension")
        return (f"accurate ({acc:.0%}) but unhurried "
                f"(median {pace:.0f}s/card) — no extension")
    except Exception:  # noqa: BLE001 -- describe must never raise
        return "too early to tell — answer a few cards first"


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Flow detection <small>(feature)</small></h3>"
        "<p>Fast and accurate means in flow: "
        "<code>groundwork/flowdetect.py</code> provides "
        "<code>in_flow()</code> (recent accuracy ≥ 80% with median pace "
        "within 45s/card over at least 3 attempts) and "
        "<code>extend_session()</code>, which the Due session calls to "
        "append up to 3 bonus cards. No history means no extension — "
        "the planned session stands.</p>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "flow-detection",
        "kind": "feature",
        "title": "Flow detection",
        "blurb": "Nailing cards quickly? The session stretches a little — accuracy plus pace earns bonus cards.",
        "path": "/status",
        "anchor": "status-b21-flowdetect",
    }
