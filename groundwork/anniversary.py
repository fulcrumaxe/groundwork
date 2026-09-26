"""Anniversary recaps (F-132): your year in code comprehension.

History spanning a year+ earns one gentle year-in-review: trailing-365-day
attempts, active days/months, concepts owned, first-half vs second-half
accuracy, top 3 modules. Private (your History page only), no streaks.
Pure + stdlib (html, datetime); block_html only reads tables. Never raises.
Year-old history gains the section; young/empty yields "" (legacy bytes).
"""
from __future__ import annotations

import html
from datetime import date, timedelta

STATUS_ANCHOR = "status-b25-anniversary"
BOX_ANCHOR = "anniversary"
YEAR_DAYS = 365
TOP_N = 3


def _coerce_str(v) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    try:
        return str(v)
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return ""


def _parse_day(v):
    try:
        t = _coerce_str(v).strip()
        if len(t) < 10:
            return None
        return date.fromisoformat(t[:10])
    except (ValueError, TypeError):
        return None


def _today(now=""):
    if isinstance(now, str) and now.strip():
        return _parse_day(now)
    if now is None or (isinstance(now, str) and not now.strip()):
        return date.today()
    return now if isinstance(now, date) else None


def span_days(first_seen, now=""):
    try:
        s, e = _parse_day(first_seen), _today(now)
        return None if s is None or e is None else max(0, (e - s).days)
    except Exception:  # noqa: BLE001 -- span must never raise
        return None


def eligible(first_seen, now="") -> bool:
    try:
        s = span_days(first_seen, now)
        return s is not None and s >= YEAR_DAYS
    except Exception:  # noqa: BLE001 -- gate must never raise
        return False


def summarize(rows, owned_n=0, now="") -> dict:
    """Pure recap: trailing-365-day stats; eligibility spans full history.

    rows: mappings/tuples of (reviewed_at, grade, module). Never raises.
    """
    blank = {"eligible": False, "attempts": 0, "passed": 0, "acc": None,
             "days": 0, "months": 0, "owned": 0, "trend": ("—", "—"), "top": []}
    try:
        end = _today(now)
        if end is None:
            return dict(blank)
        try:
            owned = max(0, int(owned_n))
        except (TypeError, ValueError):
            owned = 0
        start = end - timedelta(days=YEAR_DAYS - 1)
        mid = start + timedelta(days=YEAR_DAYS // 2)
        first, n, ok = None, 0, 0
        days, months, mods, halves = set(), set(), {}, [[0, 0], [0, 0]]
        for row in rows or []:
            try:
                if isinstance(row, dict):
                    when, grade = row.get("reviewed_at", row.get("when", "")), row.get("grade", 0)
                    label = row.get("module", row.get("summary", ""))
                else:
                    when, grade, label = row[0], row[1], row[2] if len(row) > 2 else ""
            except (TypeError, IndexError, KeyError):
                continue
            day = _parse_day(when)
            if day is None or day > end:
                continue
            if first is None or day < first:
                first = day
            if day < start:
                continue
            try:
                passed = float(grade or 0) >= 4
            except (TypeError, ValueError):
                passed = False
            n += 1
            ok += 1 if passed else 0
            days.add(day)
            months.add((day.year, day.month))
            name = _coerce_str(label).strip() or "Module"
            mods[name] = mods.get(name, 0) + 1
            h = halves[0] if day < mid else halves[1]
            h[0] += 1
            h[1] += 1 if passed else 0
        span = (end - first).days if first else 0
        pct = lambda p: f"{round(100 * p[1] / p[0])}%" if p[0] else "—"
        top = sorted(mods.items(), key=lambda kv: (-kv[1], kv[0]))[:TOP_N]
        return {"eligible": span >= YEAR_DAYS and n > 0, "attempts": n,
                "passed": ok, "acc": round(100 * ok / n) if n else None,
                "days": len(days), "months": len(months), "owned": owned,
                "trend": (pct(halves[0]), pct(halves[1])),
                "top": [{"module": k, "attempts": v} for k, v in top]}
    except Exception:  # noqa: BLE001 -- summarize must never raise
        return dict(blank)


def recap_html(recap) -> str:
    """Section HTML; "" when no recap is earned yet. Never raises."""
    try:
        if not isinstance(recap, dict) or not recap.get("eligible"):
            return ""
        n = recap.get("attempts") or 0
        if n <= 0:
            return ""
        d, m = recap.get("days") or 0, recap.get("months") or 0
        t0, t1 = recap.get("trend") or ("—", "—")
        tops = ", ".join(f"{html.escape(t.get('module', ''))} ({t.get('attempts', 0)})"
                         for t in (recap.get("top") or []) if isinstance(t, dict))
        return (f"<section id='{BOX_ANCHOR}'><h2>Your year in code comprehension</h2>"
                f"<p>{n} attempts across {d} active day{'s' if d != 1 else ''} in {m} "
                f"month{'s' if m != 1 else ''} · {recap.get('passed', 0)} passed "
                f"({recap.get('acc', 0)}%) · {recap.get('owned', 0)} concepts owned. "
                f"Accuracy trend: {t0} → {t1} (first vs second half of your year).</p>"
                f"<p>Most revisited: {tops or '—'}.</p>"
                "<p><small>Only you see this — a quiet anniversary, not a leaderboard.</small></p></section>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def block_html(db_path: str) -> str:
    """Year recap for History; "" when young/empty/hostile. Never raises."""
    try:
        from . import db as dbmod, ownership as ownmod, sched as schedmod
        now = schedmod.utcnow()
        today = now.strftime("%Y-%m-%d")
        con = dbmod.connect(db_path)
        try:
            if not eligible(con.execute("SELECT MIN(reviewed_at) FROM reviews").fetchone()[0], today):
                return ""
            # No SQL cutoff: summarize windows internally but spans
            # eligibility over the full history (old rows prove the year).
            rows = con.execute("SELECT reviews.reviewed_at AS reviewed_at, reviews.grade AS grade,"
                               " modules.task_summary AS module FROM reviews JOIN cards ON cards.id = reviews.card_id"
                               " JOIN concepts ON concepts.id = cards.concept_id JOIN modules ON modules.id = concepts.module_id").fetchall()
            owned = sum(1 for (mid,) in con.execute("SELECT id FROM modules").fetchall()
                        for _, o in ownmod.owned_map(con, mid).values() if o)
        finally:
            con.close()
        return recap_html(summarize([dict(r) for r in rows], owned, today))
    except Exception:  # noqa: BLE001 -- history never breaks
        return ""


def tour_entry() -> dict:
    """Tour registry entry for anniversary recaps."""
    return {"id": "anniversary-recap", "kind": "feature",
            "title": "Anniversary recaps",
            "blurb": ("A year in? History shows your year in code "
                      "comprehension — gentle, private, no streaks."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch25.py."""
    return (f"<h3 id='{STATUS_ANCHOR}'>Anniversary recaps <small>(feature)</small></h3>"
            "<p>Histories spanning a year gain one year-in-review on History (attempts, active days/months, owned, half-vs-half accuracy, top 3 modules) — private, kindly worded, no streaks. Young histories render exactly as before. "
            "<code>groundwork/anniversary.py</code> provides <code>eligible()</code> (365-day gate), <code>summarize()</code> (pure aggregation) and <code>block_html()</code> (History section, <code>\"\"</code> when unearned).</p>")
