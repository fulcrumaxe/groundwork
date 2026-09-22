"""Lesson-version banner: 'updated for commit X' (I-115).

A lesson names the commit it was written for; when the repo HEAD has
moved on since, the banner says so. Same or unknown commits stay
silent (byte-identical legacy path). Stdlib only (`html`, `re`);
never shells out, never raises.
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b19-lessonver"

_SHORT = re.compile(r"^[0-9a-f]{7,40}$", re.IGNORECASE)


def normalize_commit(value) -> str:
    """Lowercase hex hash (7-40 chars), else ""; never raises."""
    try:
        if not isinstance(value, str):
            return ""
        text = value.strip().lower()
        return text if _SHORT.match(text) else ""
    except Exception:  # noqa: BLE001 -- normalizing never raises
        return ""


def commits_of(value) -> list:
    """Split 'a,b', ranges 'a..b', whitespace; normalized, deduped."""
    try:
        if not isinstance(value, str) or not value.strip():
            return []
        parts = re.split(r"[\s,;]+", value.strip())
        out = []
        for p in parts:
            for piece in p.split(".."):
                norm = normalize_commit(piece)
                if norm and norm not in out:
                    out.append(norm)
        return out
    except Exception:  # noqa: BLE001
        return []


def lesson_commit_of(lesson, module_commit_range: str = "") -> str:
    """Lesson's own commit first, else last hash of the module range."""
    try:
        if isinstance(lesson, dict):
            got = normalize_commit(lesson.get("commit"))
            if got:
                return got
        hashes = commits_of(module_commit_range)
        return hashes[-1] if hashes else ""
    except Exception:  # noqa: BLE001
        return ""


def needs_banner(lesson_commit: str, current_commit: str = "") -> bool:
    """True iff both known and the lesson commit is not among current."""
    try:
        lesson = normalize_commit(lesson_commit)
        if not lesson:
            return False
        current = commits_of(current_commit)
        if not current:
            return True
        return lesson not in current
    except Exception:  # noqa: BLE001
        return False


def banner_html(lesson_commit: str, current_commit: str = "") -> str:
    """Provenance note, plus moved-on comparison when HEAD differs.

    Same/unknown commits render "" (legacy path). Full hashes display
    truncated to 7 chars. Escaped; never raises.
    """
    try:
        lesson = normalize_commit(lesson_commit)
        if not lesson:
            return ""
        current = commits_of(current_commit)
        if current and lesson in current:
            return ""
        short = lesson[:7]
        if not current:
            return (
                f"<p class='lessonver'>Updated for commit "
                f"<code>{html.escape(short)}</code>.</p>")
        now = html.escape(current[-1][:7])
        return (
            f"<p class='lessonver'>Updated for commit "
            f"<code>{html.escape(short)}</code> — code has moved on since "
            f"(now at <code>{now}</code>).</p>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def banner_anchor_html(lesson_commit: str, current_commit: str = "") -> str:
    """Banner with id='lessonver' for the first lesson section; "" when none."""
    try:
        banner = banner_html(lesson_commit, current_commit)
        if not banner:
            return ""
        return banner.replace("<p class='lessonver'>",
                              "<p class='lessonver' id='lessonver'>", 1)
    except Exception:  # noqa: BLE001
        return ""


def banner_css() -> str:
    """Raw declarations only (no <style> tags); palette tokens."""
    return (".lessonver{color:var(--ink);background:var(--paper);"
            "padding:2px 0;}")


def section_html() -> str:
    """Anchored status subsection; joined by the batch19 home module."""
    sample = banner_html("abc1234abc1234abc1234abc1234abc1234abcd",
                         "def5678def5678def5678def5678def5678def5")
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Lesson version banner <small>(improvement)</small></h3>"
        "<p>Lessons name the commit they were written for — and say when "
        "the code has moved on since. <code>groundwork/lessonver.py</code> "
        "compares the lesson's recorded commit against the repo HEAD on the "
        "lesson rendering path (<code>lessons.render_levels</code>); same or "
        "unknown commits render nothing. A live sample renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "lesson-version",
        "kind": "improvement",
        "title": "Lesson version banner",
        "blurb": "Lessons name the commit they were written for — and say "
                 "when the code has moved on since.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
