"""Quiet celebrations: motion-free milestone and session twins (F-142).

Milestones and session wins get a still twin with typographic delight
(CSS ring seals, [x] marks, letterspaced heading -- no keyframes at
all), hidden until claimed. ``prefers-reduced-motion`` reveals it via
CSS alone; ``?calm=1`` shows it server-side with a carry-over toggle
link. Empty histories get "" so legacy bytes never change.

Caller path (History page, never a Status demo):
``history.history_html`` joins ``block_html(db_path, query)`` onto the
milestones line. ``query`` already arrives parsed (parse_qs shape), so
?calm= needs no signature change anywhere. No DB/schema changes, no
JS wire (CSS-only reveal), never raises.
"""
from __future__ import annotations

import html
from urllib.parse import urlencode

STATUS_ANCHOR = "status-b26-calmjoy"
TWIN_ID = "calm-joy"
CALM_PARAM = "calm"
PASS_GRADE = 4

_CALM_ON = ("1", "true", "yes", "on", "calm")
_CALM_OFF = ("0", "false", "no", "off")


def is_calm(query) -> bool:
    """True when ?calm= asks for the still variant. Fail closed False."""
    try:
        if isinstance(query, str):
            text = query.strip().lower()
            if text in _CALM_ON:
                return True
            if text in _CALM_OFF:
                return False
            if "=" in text:
                from urllib.parse import parse_qs
                try:
                    return is_calm(parse_qs(text))
                except Exception:  # noqa: BLE001 -- parse never raises out
                    return False
            return False
        if not isinstance(query, dict):
            return False
        raw = query.get(CALM_PARAM, [])
        if isinstance(raw, str):
            vals = [raw]
        elif isinstance(raw, (list, tuple)):
            vals = list(raw)
        else:
            vals = [raw]
        result, found = False, False
        for v in vals:
            try:
                tok = str(v).strip().lower()
            except Exception:  # noqa: BLE001 -- one bad value never breaks
                continue
            if tok in _CALM_ON:
                result, found = True, True
            elif tok in _CALM_OFF:
                result, found = False, True
        return result if found else False
    except Exception:  # noqa: BLE001 -- gate must never raise
        return False


def _carry_href(query, calm: bool) -> str:
    """History href preserving query params while setting calm."""
    try:
        path = "/reviews"
        pairs = []
        if isinstance(query, dict):
            for key in sorted(query):
                try:
                    name = str(key)
                except Exception:  # noqa: BLE001 -- one bad key never breaks
                    continue
                if name == CALM_PARAM:
                    continue
                vals = query[key]
                if isinstance(vals, (list, tuple)):
                    first = vals[0] if vals else ""
                else:
                    first = vals
                try:
                    pairs.append((name, str(first)))
                except Exception:  # noqa: BLE001 -- one bad value never breaks
                    continue
        if calm:
            pairs.append((CALM_PARAM, "1"))
        if not pairs:
            return path
        return path + "?" + urlencode(pairs)
    except Exception:  # noqa: BLE001 -- links must never raise
        return "/reviews"


def toggle_html(query=None, calm=None) -> str:
    """Calm/Full view toggle with query carry-over. Never raises."""
    if calm is None:
        calm = is_calm(query)
    try:
        if calm:
            href = html.escape(_carry_href(query, False), quote=True)
            return ("<p class='calm-joy-toggle'><small>Calm view on: still "
                    "type, no motion. "
                    f"<a href='{href}'>Full view</a></small></p>")
        href = html.escape(_carry_href(query, True), quote=True)
        return ("<p class='calm-joy-toggle'><small>Prefer still celebrations? "
                f"<a href='{href}'>Calm view</a></small></p>")
    except Exception:  # noqa: BLE001 -- links must never raise
        return ("<p class='calm-joy-toggle'><small>"
                "<a href='/reviews?calm=1'>Calm view</a></small></p>")


def celebrate_css() -> str:
    """Raw CSS declarations for the twin; NEVER <style> tags.

    Static only: zero keyframes, zero animation declarations, so
    motion.audit_css() always passes. The twin hides via [hidden]
    until the reduced-motion media query or the force-calm class
    claims it -- no JS wire needed.
    """
    try:
        return (
            ".calm-joy-toggle{margin:.5rem 0;color:inherit}"
            ".calm-joy-twin{display:block;box-sizing:border-box;width:100%;"
            "border:1px solid currentColor;border-radius:10px;"
            "padding:.75rem 1rem;margin:.75rem 0}"
            ".calm-joy-twin[hidden]{display:none}"
            ".calm-joy-twin h2{margin:0 0 .25rem;letter-spacing:.02em}"
            ".calm-joy-twin ul{margin:.5rem 0;padding-left:1.25rem}"
            ".calm-joy-twin li{margin:.2rem 0}"
            ".calm-joy-twin .seal{display:inline-block;width:.6em;height:.6em;"
            "margin-right:.4em;border:.14em solid currentColor;border-radius:50%;"
            "vertical-align:baseline}"
            ".calm-joy-session{margin:.5rem 0;font-weight:700}"
            "@media(prefers-reduced-motion:reduce){"
            ".calm-joy-twin[hidden]{display:block}}"
            ".calm-joy-twin.force-calm[hidden]{display:block}"
        )
    except Exception:  # noqa: BLE001 -- CSS must never raise
        return ".calm-joy-twin{display:block}"


def _field(moment, name: str):
    """Defensive field read over dicts and sqlite Rows."""
    try:
        if isinstance(moment, dict):
            return moment.get(name, "")
        return moment[name]
    except Exception:  # noqa: BLE001 -- reads must never raise
        return ""


def milestone_line(moment) -> str:
    """One static milestone row; "" when the row says nothing."""
    try:
        try:
            label = str(_field(moment, "label") or "").strip()
        except Exception:  # noqa: BLE001 -- coercion never raises
            label = ""
        try:
            day = str(_field(moment, "when") or "").strip()[:10]
        except Exception:  # noqa: BLE001 -- coercion never raises
            day = ""
        if not label:
            return ""
        safe = html.escape(label, quote=True)
        seal = "<span class='seal' aria-hidden='true'></span>"
        if day:
            return (f"<li>{seal}<b>{safe}</b> "
                    f"<small>{html.escape(day, quote=True)}</small></li>")
        return f"<li>{seal}<b>{safe}</b></li>"
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def session_line(summary) -> str:
    """Still session-win line over summarize() math; "" when quiet."""
    try:
        if not isinstance(summary, dict):
            return ""
        try:
            answered = int(summary.get("answered", 0) or 0)
        except (TypeError, ValueError):
            return ""
        if answered <= 0:
            return ""
        try:
            correct = int(summary.get("correct", 0) or 0)
        except (TypeError, ValueError):
            correct = 0
        try:
            acc = int(summary.get("accuracy", 0) or 0)
        except (TypeError, ValueError):
            acc = 0
        correct = max(0, min(correct, answered))
        acc = max(0, min(acc, 100))
        try:
            nxt = str(summary.get("next_due", "") or "").strip() or "-"
        except Exception:  # noqa: BLE001 -- coercion never raises
            nxt = "-"
        return (f"<p class='calm-joy-session'>[x] {answered} answered today, "
                f"{correct} correct ({acc}%). "
                f"Next due {html.escape(nxt, quote=True)}.</p>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def twin_html(moments, summary, query=None) -> str:
    """Toggle plus hidden twin; "" when no wins exist (legacy bytes)."""
    try:
        rows = moments if isinstance(moments, (list, tuple)) else []
        items = "".join(m for m in (milestone_line(m) for m in rows) if m)
        sess = session_line(summary)
        if not items and not sess:
            return ""
        calm = is_calm(query)
        if calm:
            open_tag = f"<div class='calm-joy-twin force-calm' id='{TWIN_ID}'>"
        else:
            open_tag = f"<div class='calm-joy-twin' id='{TWIN_ID}' hidden>"
        body = "<h2>Quiet celebrations</h2>"
        body += ("<p>Big milestones, still pixels: everything below is "
                 "already earned. No timers, no streaks, no motion.</p>")
        if items:
            body += f"<ul>{items}</ul>"
        if sess:
            body += sess
        return toggle_html(query, calm) + open_tag + body + "</div>"
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def today_summary(db_path: str) -> dict:
    """Today's answered/correct/accuracy/next-due; blank when quiet."""
    blank = {"answered": 0, "correct": 0, "accuracy": 0, "next_due": ""}
    try:
        from . import db as dbmod
        from . import sched as schedmod
        from . import session as sessionmod
        try:
            today = schedmod.utcnow().strftime("%Y-%m-%d")
        except Exception:  # noqa: BLE001 -- clock never raises out
            today = ""
        con = dbmod.connect(db_path)
        try:
            grades = []
            if today:
                grades = [r[0] for r in con.execute(
                    "SELECT grade FROM reviews WHERE substr(reviewed_at, 1, 10)=?",
                    (today,)).fetchall()]
            nxt = con.execute("SELECT MIN(due) FROM cards").fetchone()
        finally:
            con.close()
        out = sessionmod.summarize([{"grade": g} for g in grades])
        try:
            raw = nxt[0] if nxt else ""
            out["next_due"] = str(raw or "")[:10]
        except Exception:  # noqa: BLE001 -- date slice never raises out
            out["next_due"] = ""
        return out
    except Exception:  # noqa: BLE001 -- stats never raise
        return dict(blank)


def block_html(db_path: str, query=None) -> str:
    """History caller: calm twin for milestones + today; "" when quiet."""
    try:
        from . import milestones as milesmod
        moments = milesmod.moments(db_path)
        summary = today_summary(db_path)
        return twin_html(moments, summary, query)
    except Exception:  # noqa: BLE001 -- history never breaks
        return ""


def status_section_html() -> str:
    """Anchored status subsection; joined by the parent batch module."""
    try:
        sample = twin_html(
            [{"label": "First concept owned", "when": "2026-09-12T10:00:00Z"},
             {"label": "10th module practiced", "when": "2026-09-20T10:00:00Z"}],
            {"answered": 12, "correct": 10, "accuracy": 83,
             "next_due": "2026-09-28"},
            {"calm": ["1"]})
    except Exception:  # noqa: BLE001 -- sample never raises out
        sample = ""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Quiet celebrations "
            "<small>(feature)</small></h3>"
            "<p>Milestones and session wins get a still twin: "
            "<code>groundwork/calmjoy.py</code> restates earned milestones "
            "plus today's answered/correct/next-due in static type (CSS ring "
            "seals, [x] marks, no keyframes at all), hidden until claimed. "
            "<code>prefers-reduced-motion</code> reveals it via CSS alone; "
            "<code>?calm=1</code> shows it server-side with a carry-over "
            "toggle. Empty histories render exactly as before. "
            "A live sample renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Quiet celebrations</h3>"
                "<p>Quiet-celebration help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour registry entry for quiet celebrations."""
    return {
        "id": "calm-joy",
        "kind": "feature",
        "title": "Quiet celebrations",
        "blurb": ("Milestones and session wins, restated still -- calm by "
                  "default for reduced-motion users, one click away for "
                  "everyone."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
