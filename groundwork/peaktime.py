"""Optimal review-time suggestions (F-92): review when recall peaks.

Past grades bucketed into four dayparts reveal when recall runs
hottest; the Due queue banners the winning window once three or more
reviews exist. Thinner histories omit the banner, so Due renders
exactly as today. Rows are (grade, reviewed_at) pairs — the shape
History already queries. Stdlib only (``html``); no I/O, never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b20-peaktime"

MIN_ATTEMPTS = 3
PASS_GRADE = 3

WINDOWS = ("morning", "midday", "evening", "night")


def bucket_for(hour) -> str:
    """Daypart for an hour 0-23; "morning" on hostile input."""
    try:
        hour = int(hour) % 24
    except (TypeError, ValueError):
        return "morning"
    if 5 <= hour < 11:
        return "morning"
    if 11 <= hour < 17:
        return "midday"
    if 17 <= hour < 23:
        return "evening"
    return "night"


def _hour_of(when) -> int | None:
    try:
        text = str(when or "").strip()
        if "T" not in text:
            return None
        return int(text.split("T", 1)[1][:2])
    except (TypeError, ValueError, IndexError):
        return None


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize(rows) -> dict:
    """{window: {n, pass_rate}}; unparseable rows are skipped."""
    try:
        counts = {w: [0, 0] for w in WINDOWS}
        for row in rows or []:
            try:
                if isinstance(row, dict):
                    grade, when = row.get("grade"), row.get("reviewed_at")
                else:
                    grade, when = row[0], row[1]
            except (TypeError, IndexError, KeyError):
                continue
            grade = _num(grade)
            hour = _hour_of(when)
            if grade is None or hour is None:
                continue
            slot = counts[bucket_for(hour)]
            slot[1] += 1
            if grade >= PASS_GRADE:
                slot[0] += 1
        return {w: {"n": counts[w][1],
                    "pass_rate": (counts[w][0] / counts[w][1]
                                  if counts[w][1] else 0.0)}
                for w in WINDOWS}
    except Exception:  # noqa: BLE001
        return {w: {"n": 0, "pass_rate": 0.0} for w in WINDOWS}


def suggest(rows) -> dict:
    """{window, label, pass_rate, n}; fallback below 3 attempts."""
    try:
        table = summarize(rows)
        total = sum(v["n"] for v in table.values())
        if total < MIN_ATTEMPTS:
            return {"window": None, "label": "no peak yet",
                    "pass_rate": 0.0, "n": total}
        ranked = sorted(WINDOWS,
                        key=lambda w: (-table[w]["pass_rate"],
                                       -table[w]["n"], WINDOWS.index(w)))
        best = ranked[0]
        return {"window": best, "label": best,
                "pass_rate": table[best]["pass_rate"],
                "n": table[best]["n"]}
    except Exception:  # noqa: BLE001
        return {"window": None, "label": "no peak yet",
                "pass_rate": 0.0, "n": 0}


def describe(rows) -> str:
    """One-line verdict; the no-data fallback names the threshold."""
    try:
        got = suggest(rows)
        if got["window"] is None:
            return ("No peak yet — answer 3+ reviews across the day "
                    "and I will name your best window.")
        rate = round(100 * got["pass_rate"])
        return (f"Peak recall: {got['label']} "
                f"({rate}% passes over {got['n']} reviews).")
    except Exception:  # noqa: BLE001
        return "No peak yet."


def banner_html(rows) -> str:
    """Due-queue banner; "" below the attempts threshold."""
    try:
        got = suggest(rows)
        if got["window"] is None:
            return ""
        return (f"<p id='peaktime'>Peak recall: "
                f"{html.escape(got['label'])} — review then for more "
                f"passes.</p>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    sample = banner_html([(5, "2020-01-01T19:00:00Z")] * 4)
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Best time to review <small>(feature)</small></h3>"
        "<p>Your past grades reveal when your recall peaks — review then "
        "for more passes. <code>groundwork/peaktime.py</code> buckets "
        "reviews into four dayparts on the Due queue "
        "(<code>Handler.due_html</code>); thin histories show no banner. "
        "A live sample renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "recall-peak-time",
        "kind": "feature",
        "title": "Best time to review",
        "blurb": "Your past grades reveal when your recall peaks — "
                 "review then for more passes.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
