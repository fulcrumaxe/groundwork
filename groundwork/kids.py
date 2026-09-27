"""Kids mode (F-141): easy words, big targets, parent dashboard.

`?kids=1` on the History page switches three small things: a fixed
word-substitution map over live rendered text (tag-aware; tags, ids,
hrefs, and code/pre/script/style regions pass through untouched), a
bigger-target `.kids` CSS class on the body, and a parent dashboard
with live counts from existing tables (modules, due, attempts). No
reading level engine, no schema change: without `?kids=1` every entry
point returns its input unchanged, so legacy pages keep byte-identical
HTML. Caller: history.history_html (both return points); the CSS joins
the head wire in web.py. Never raises.
"""
from __future__ import annotations

import html
import re
from datetime import datetime, timezone

from . import db as dbmod

STATUS_ANCHOR = "status-b26-kids"
BOX_ANCHOR = "kids-mode"
DASH_ANCHOR = "parent-dash"

# Fixed kid-friendlier vocabulary: lowercase source -> simpler words.
# Single words only; plurals get their own keys. Word boundaries keep
# identifiers such as "submitted" or "re-executed" untouched.
WORDS = {
    "utilize": "use",
    "approximately": "about",
    "demonstrate": "show",
    "comprehension": "understanding",
    "comprehend": "understand",
    "evaluate": "rate",
    "configuration": "settings",
    "configure": "set up",
    "repository": "project",
    "retrieve": "get",
    "commence": "start",
    "implement": "build",
    "execute": "run",
    "initialize": "start",
    "submit": "send",
    "accuracy": "score",
    "attempt": "try",
    "attempts": "tries",
    "exercise": "practice",
    "exercises": "practice",
}

_RULES = [(re.compile(r"\b" + w + r"\b", re.IGNORECASE), rep)
          for w, rep in WORDS.items()]

_SPLIT_RE = re.compile(r"(<[^>]*>)")
_OPEN_RE = re.compile(r"<\s*(code|pre|script|style)\b", re.IGNORECASE)
_CLOSE_RE = re.compile(r"<\s*/\s*(code|pre|script|style)\s*>", re.IGNORECASE)


def is_kids(query) -> bool:
    """True only when the parsed query carries kids=1; never raises.

    Accepts the parse_qs dict history_html already receives (values
    are lists), a bare "1" string, or True; everything else is False.
    """
    try:
        if isinstance(query, dict):
            vals = query.get("kids", [])
            if isinstance(vals, str):
                vals = [vals]
            for v in vals or []:
                if v is True or str(v).strip() == "1":
                    return True
            return False
        if isinstance(query, str):
            return query.strip() == "1"
        return query is True
    except Exception:  # noqa: BLE001 -- gate must never raise
        return False


def _case_match(word: str, rep: str) -> str:
    """Replacement matching the matched word's case (lower/Title/UPPER)."""
    if word.isupper():
        return rep.upper()
    if word[:1].isupper():
        return rep.capitalize()
    return rep


def simplify(text):
    """Plain-text word substitution; non-strings pass through unchanged."""
    try:
        if not isinstance(text, str):
            return text
        out = text
        for rx, rep in _RULES:
            out = rx.sub(lambda m, r=rep: _case_match(m.group(0), r), out)
        return out
    except Exception:  # noqa: BLE001 -- text must never raise
        return text


def simplify_html(page):
    """Substitute text nodes only; tags and code regions stay identical."""
    try:
        if not isinstance(page, str):
            return page
        out = []
        skip = 0
        for chunk in _SPLIT_RE.split(page):
            if not chunk:
                continue
            if chunk.startswith("<") and chunk.endswith(">"):
                if _OPEN_RE.match(chunk):
                    skip += 1
                elif _CLOSE_RE.match(chunk):
                    skip = max(0, skip - 1)
                out.append(chunk)
            else:
                out.append(simplify(chunk) if skip == 0 else chunk)
        return "".join(out)
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return page


def kids_css() -> str:
    """Bigger-target rules for the .kids wrapper; raw head-wire text."""
    return (
        ".kids{font-size:1.12rem;line-height:1.6}"
        ".kids p,.kids li{max-width:64ch}"
        ".kids button,.kids a.btn,.kids input[type=submit]{"
        "min-height:3rem;padding:.8rem 1.2rem;font-size:1.15rem;"
        "border-radius:.6rem}"
        ".kids a{display:inline-block;padding:.2rem .1rem}")


def banner_html() -> str:
    """On-state banner with turn-off and dashboard links."""
    return (
        f"<p id='{BOX_ANCHOR}'><b>Kids mode is on:</b> easy words, "
        "big buttons. <a href='/reviews'>Turn off</a> | "
        f"<a href='#{DASH_ANCHOR}'>Parent dashboard</a></p>")


def _counts(db_path: str) -> tuple:
    """(modules, due, tries, passed) from existing tables; zeros on error."""
    try:
        if not db_path:
            return (0, 0, 0, 0)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con = dbmod.connect(db_path)
        try:
            mods = con.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
            due = con.execute(
                "SELECT COUNT(*) FROM cards WHERE due <= ? AND stale = 0",
                (now,)).fetchone()[0]
            row = con.execute(
                "SELECT COUNT(*), COALESCE(SUM(CASE WHEN grade >= 4 "
                "THEN 1 ELSE 0 END), 0) FROM reviews").fetchone()
            return (mods or 0, due or 0, row[0] or 0, row[1] or 0)
        finally:
            con.close()
    except Exception:  # noqa: BLE001 -- counts must never raise
        return (0, 0, 0, 0)


def parent_html(db_path: str = "") -> str:
    """Parent dashboard: live counts in plain words; never raises."""
    try:
        mods, due, tries, passed = _counts(db_path)
        return (
            f"<section id='{DASH_ANCHOR}'><h2>Parent dashboard</h2>"
            f"<p>{mods} projects | {due} cards due | {tries} tries | "
            f"{passed} passed.</p>"
            "<p><small>Big-picture counts only. Full detail stays on "
            "<a href='/reviews?kids=1'>History in kids mode</a>.</small></p>"
            "</section>")
    except Exception:  # noqa: BLE001 -- dashboard must never raise
        return ""


def page_html(body_html, query=None, db_path: str = "") -> str:
    """Kids-mode page wrap; input unchanged unless ?kids=1. Never raises."""
    try:
        if not is_kids(query):
            return body_html
        if not isinstance(body_html, str):
            return body_html
        return ("<div class='kids'>" + banner_html()
                + simplify_html(body_html) + parent_html(db_path) + "</div>")
    except Exception:  # noqa: BLE001 -- wrap must never raise
        return body_html


def tour_entry() -> dict:
    """Tour registry entry for kids mode."""
    return {"id": "kids-mode", "kind": "feature",
            "title": "Kids mode",
            "blurb": ("Easy words, big buttons and a parent dashboard: "
                      "add ?kids=1 on the History page."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection with a live word-map demo."""
    try:
        before = "We utilize this configuration to evaluate attempts."
        after = simplify(before)
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Kids mode <small>(feature)</small></h3>"
            "<p>Add <code>?kids=1</code> on the History page for easy words "
            "(a small fixed map, code regions skipped), big buttons (one "
            "<code>.kids</code> CSS class), and a parent dashboard with live "
            "module, due and attempt counts. <code>groundwork/kids.py</code> "
            "wraps <code>history.history_html</code>; without the flag the "
            "page renders byte-identical. Live demo: "
            f"<code>{html.escape(before)}</code> becomes "
            f"<code>{html.escape(after)}</code>.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Kids mode</h3>"
                "<p>Kids help temporarily unavailable.</p>")
