"""Time-invested ledger: hours in, owned concepts out (F-105).

Every practice day contributes its active span (last review minus
first review, capped per day so an open tab never invents a marathon)
and the ledger divides by owned concepts for a minutes-per-concept
ROI. Pure computation over the existing reviews table plus the
headline owned count — no schema change, no new storage.

Caller path (History page, never a Status demo):
``history.history_html`` appends ``section_html`` in both branches.
The section always renders (anchor-stable for the tour); quiet weeks
get a ledger-to-fill line instead of numbers. Never raises.
"""
from __future__ import annotations

from . import db as dbmod
from . import ownhead as ownheadmod

STATUS_ANCHOR = "status-b22-timeledger"

#: A day never contributes more than this; tabs stay open, ledgers lie.
DAY_CAP_MINUTES = 360.0


def daily_spans(db_path: str) -> list:
    """[(day, minutes)] oldest-first, capped per day.

    Empty/hostile DB yields []; never raises.
    """
    try:
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT substr(reviewed_at, 1, 10) AS d,"
                " MIN(reviewed_at) AS lo, MAX(reviewed_at) AS hi,"
                " COUNT(*) AS n FROM reviews GROUP BY d"
                " ORDER BY d").fetchall()
        finally:
            con.close()
    except Exception:  # noqa: BLE001 -- stats never raise
        return []
    out = []
    for r in rows:
        try:
            lo, hi = str(r["lo"] or ""), str(r["hi"] or "")
            minutes = max(0.0, (_stamp(hi) - _stamp(lo)) / 60.0)
            out.append((str(r["d"] or ""), min(DAY_CAP_MINUTES, minutes)))
        except Exception:  # noqa: BLE001 -- one bad day skips itself
            continue
    return out


def _stamp(raw: str) -> float:
    """Epoch seconds for an ISO-ish timestamp; "" yields 0.0."""
    from datetime import datetime, timezone
    try:
        text = str(raw or "").strip().replace("Z", "+00:00")
        return datetime.fromisoformat(text).replace(
            tzinfo=timezone.utc).timestamp()
    except Exception:  # noqa: BLE001 -- bad stamps read as zero
        return 0.0


def ledger(db_path: str) -> dict:
    """{"minutes": float, "days": int, "owned": int}.

    Hostile input yields zeros; never raises.
    """
    try:
        spans = daily_spans(db_path)
        owned = int(ownheadmod.counts(db_path)["owned"])
        return {"minutes": round(sum(m for _, m in spans), 1),
                "days": len(spans),
                "owned": owned}
    except Exception:  # noqa: BLE001 -- ledger never raises
        return {"minutes": 0.0, "days": 0, "owned": 0}


def _fmt_minutes(minutes) -> str:
    try:
        total = max(0, int(round(float(minutes))))
    except Exception:  # noqa: BLE001 -- formatting never raises
        total = 0
    h, m = divmod(total, 60)
    if h:
        return f"{h}h {m}m"
    return f"{m}m"


def section_html(db_path: str) -> str:
    """Always-rendered History section; the anchor never moves."""
    try:
        L = ledger(db_path)
        if L["days"] <= 0:
            body = ("<p>No invested time on the books yet — your first "
                    "practice day opens the ledger.</p>")
        else:
            roi = ""
            if L["owned"] > 0:
                roi = (f" — about {_fmt_minutes(L['minutes'] / L['owned'])}"
                       " per owned concept")
            body = (f"<p><b>{_fmt_minutes(L['minutes'])}</b> invested "
                    f"across {L['days']} day{'s' if L['days'] != 1 else ''} "
                    f"→ <b>{L['owned']} owned</b>{roi}.</p>")
        return f"<h2 id='time-ledger'>Time ledger</h2>{body}"
    except Exception:  # noqa: BLE001 -- history never breaks
        return ("<h2 id='time-ledger'>Time ledger</h2>"
                "<p>Ledger temporarily unavailable.</p>")


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Time ledger "
            "<small>(feature)</small></h3>"
            "<p>Hours in, owned concepts out — "
            "<code>groundwork/timeledger.py</code> sums capped daily "
            "active spans from the existing reviews table and divides by "
            "the headline owned count for a minutes-per-concept ROI, on "
            "the History page in both branches.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Time ledger</h3>"
                "<p>Ledger help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "time-ledger",
        "kind": "feature",
        "title": "Time ledger",
        "blurb": ("Your invested hours against concepts owned — the "
                  "honest ROI of practice."),
        "path": "/reviews",
        "anchor": "time-ledger",
    }
