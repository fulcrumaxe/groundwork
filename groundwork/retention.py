"""Desired-retention setting with workload preview (I-202).

Learners pick how well they want to remember (0.70-0.95) via
``?retention=`` on the History page — bookmarkable, no cookies, no
schema, exactly like the difficulty dial's ``?dial=``. The box shows
what that target costs: projected reviews due within 7 and 30 days
if every card were re-due under the chosen target.

Honesty note: this is a what-if projection, not scheduling. The
scheduler (sched.review_card) takes no retention input — intervals
derive from stability alone — so there is no honest queue floor to
apply, and the stored due dates never move. The preview replays the
FSRS curve R(t) = (1 + t/9S)^-1 per card: under target r, a card
last reviewed at T with stability S returns at T + 9S(1/r - 1)
days. At the 0.90 default that collapses to round(S) — the stored
rule — so the default preview reproduces the live forecast (modulo
the pass-streak stretch, which the projection ignores and says
so). Never-reviewed cards keep their stored due date: no last
review means no curve to replay yet.

Overdue projections clamp to today (due now is due now); the
sibling forecast drops them off the graph's left edge instead.
Read-only over existing tables; never raises; never writes.
"""
from __future__ import annotations

from datetime import timedelta

from . import db as dbmod
from . import sched as schedmod

STATUS_ANCHOR = "status-b29-retention"

BOX_ANCHOR = "retention"

MIN_RETENTION = 0.7
MAX_RETENTION = 0.95
DEFAULT_RETENTION = 0.9

PRESETS = (0.70, 0.80, 0.90, 0.95)

HORIZON_DAYS = 30
NEAR_DAYS = 7


def normalize(value) -> float:
    """Coerce anything to a retention in [0.7, 0.95].

    Numerics clamp to the range; bools, NaN/inf, unparseable
    strings, and everything else fail closed to the 0.9 default.
    Never raises.
    """
    try:
        if isinstance(value, bool):
            return DEFAULT_RETENTION
        if isinstance(value, str):
            num = float(value.strip())
        else:
            num = float(value)
        if num != num or num in (float("inf"), float("-inf")):
            return DEFAULT_RETENTION
        return min(MAX_RETENTION, max(MIN_RETENTION, num))
    except (TypeError, ValueError):
        return DEFAULT_RETENTION
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return DEFAULT_RETENTION


def from_query(query) -> float:
    """Retention from a parse_qs dict, scalar, or None; never raises.

    A missing or empty ``?retention=`` is the 0.9 default, so the
    legacy no-param path renders exactly the default box.
    """
    try:
        if query is None:
            return DEFAULT_RETENTION
        if isinstance(query, dict):
            vals = query.get("retention", [])
            if isinstance(vals, str):
                vals = [vals]
            if not vals:
                return DEFAULT_RETENTION
            return normalize(vals[0])
        if isinstance(query, (list, tuple)):
            return normalize(query[0]) if query else DEFAULT_RETENTION
        return normalize(query)
    except Exception:  # noqa: BLE001 -- parsing must never raise
        return DEFAULT_RETENTION


def interval_for(stability, retention=None) -> int:
    """Days a card with stability S stays above target r: 9S(1/r-1).

    The FSRS curve solved for the target: at r=0.9 this is
    round(S) — the stored scheduler rule. Hostile stability fails
    closed to S=1.0; retention normalizes (None is the default).
    Never raises; at least 1 day.
    """
    try:
        r = DEFAULT_RETENTION if retention is None else normalize(retention)
        s = float(stability)
        if s != s or s <= 0:
            s = 1.0
        return max(1, round(9.0 * s * (1.0 / r - 1.0)))
    except (TypeError, ValueError):
        return 1
    except Exception:  # noqa: BLE001 -- math must never raise
        return 1


def project_due(last_review_iso, due_iso, stability,
                retention=None) -> str:
    """What-if due ISO under the target; stored due on hostile input.

    Cards with no last review (never attempted) keep their stored
    due date — there is no curve to replay yet. Never raises.
    """
    try:
        stored = due_iso if isinstance(due_iso, str) and due_iso else ""
        if not isinstance(last_review_iso, str) or not last_review_iso:
            return stored
        try:
            base = schedmod.parse_iso(last_review_iso)
        except ValueError:
            return stored
        gap = interval_for(stability, retention)
        return schedmod.iso(base + timedelta(days=gap))
    except Exception:  # noqa: BLE001 -- projection must never raise
        return due_iso if isinstance(due_iso, str) else ""


def preview_buckets(db_path: str, retention=None,
                    days: int = HORIZON_DAYS) -> list[tuple[str, int]]:
    """(date, projected-due-count) for the next `days` days.

    Same shape as workload.buckets, but over what-if due dates at
    the chosen retention; projections clamp to today so overdue
    cards count as due now. retention None (or a query dict) is
    the default; bad `days` falls back to 30. Never raises — a
    dead DB yields zeros, like an empty forecast.
    """
    try:
        days = int(days)
    except (TypeError, ValueError):
        days = HORIZON_DAYS
    days = min(90, max(1, days))
    try:
        if isinstance(retention, dict):
            r = from_query(retention)
        elif retention is None:
            r = DEFAULT_RETENTION
        else:
            r = normalize(retention)
        now = schedmod.utcnow()
        today = now.strftime("%Y-%m-%d")
        con = dbmod.connect(db_path)
        try:
            cards = con.execute(
                "SELECT id, stability, due FROM cards"
                " WHERE stale = 0").fetchall()
            last = {row["card_id"]: row["lr"] for row in con.execute(
                "SELECT card_id, MAX(reviewed_at) AS lr FROM reviews"
                " GROUP BY card_id").fetchall()}
        finally:
            con.close()
        have: dict[str, int] = {}
        for c in cards:
            try:
                proj = project_due(last.get(c["id"]), c["due"],
                                   c["stability"], r)
                day = (proj or "")[:10]
            except Exception:  # noqa: BLE001 -- one bad row skips
                continue
            if not day:
                continue
            if day < today:
                day = today
            have[day] = have.get(day, 0) + 1
        out = []
        for i in range(days):
            day = (now + timedelta(days=i)).strftime("%Y-%m-%d")
            out.append((day, have.get(day, 0)))
        return out
    except Exception:  # noqa: BLE001 -- preview must never raise
        try:
            now = schedmod.utcnow()
            return [((now + timedelta(days=i)).strftime("%Y-%m-%d"), 0)
                    for i in range(days)]
        except Exception:  # noqa: BLE001
            return []


def _counts(db_path: str, retention: float) -> tuple[int, int, int]:
    """(near-7-day, full-30-day, peak-per-day) projected load."""
    rows = preview_buckets(db_path, retention, HORIZON_DAYS)
    near = sum(n for _, n in rows[:NEAR_DAYS])
    total = sum(n for _, n in rows)
    peak = max((n for _, n in rows), default=0)
    return near, total, peak


def box_html(db_path: str, query=None) -> str:
    """History-page box: preset links plus the live preview line.

    `query` is the parse_qs dict already in scope in history_html;
    None renders the default (legacy path). Never raises.
    """
    try:
        active = from_query(query)
        links = " · ".join(
            f"<a href='/reviews?retention={p:.2f}'>{p:.2f}</a>"
            + (" <b>(active)</b>" if abs(p - active) < 0.005 else "")
            for p in PRESETS)
        near, total, peak = _counts(db_path, active)
        return (
            f"<h2 id='{BOX_ANCHOR}'>Desired retention</h2>"
            f"<p><small>Target recall strength: {links}<br>"
            f"At {active:.2f}: {near} due within 7 days, {total} "
            f"within 30 days (peak {peak}/day). What-if only — "
            f"stored due dates never move; the projection replays "
            f"the FSRS curve from each card's last review (streak "
            f"stretch ignored).</small></p>")
    except Exception:  # noqa: BLE001 -- box must never break history
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the parent batch module."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Desired retention "
            "<small>(improvement)</small></h3>"
            "<p>Pick how well you want to remember — 0.70 to 0.95 via "
            "<code>?retention=</code> on the History page — and see "
            "what it costs before committing: projected reviews due "
            "within 7 and 30 days. <code>groundwork/retention.py</code> "
            "provides <code>normalize()</code> (clamped, fails closed "
            "to 0.9, never raises), <code>interval_for()</code> (the "
            "FSRS curve solved for the target), and "
            "<code>preview_buckets()</code> (live per-day projection "
            "from each card's last review). No scheduler floor: "
            "<code>sched.review_card</code> takes no retention input, "
            "so filtering the queue would mislabel filtering as "
            "scheduling — the preview is honestly what-if, and 0.9 "
            "reproduces the stored round-S rule.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return f"<h3 id='{STATUS_ANCHOR}'>Desired retention</h3>"


def tour_entry() -> dict:
    """Tour registry entry for the retention setting."""
    # Live target: the box renders on History whenever the learner
    # has review data (the tour fixture submits one review, so the
    # gate lands here; the young-fixture pagesnap takes the empty
    # branch without it).
    try:
        return {
            "id": "desired-retention",
            "kind": "improvement",
            "title": "Desired retention",
            "blurb": ("Set how well you want to remember (0.70-0.95) "
                      "and preview the workload it costs — due within "
                      "7 and 30 days, before you commit."),
            "path": "/reviews",
            "anchor": BOX_ANCHOR,
        }
    except Exception:  # noqa: BLE001 -- tour entry must never raise
        return {"id": "desired-retention", "kind": "improvement",
                "title": "Desired retention", "blurb": "",
                "path": "/reviews", "anchor": BOX_ANCHOR}
