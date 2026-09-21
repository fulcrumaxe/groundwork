"""Session-complete hero for the empty Due queue (I-70).

When nothing is due, the queue renders a calm full-width banner: a
static inline-SVG illustration (currentColor, no emoji, no motion)
plus today's answered count, accuracy, and next-due line — with the
existing next-action links kept so the no-dead-end contract holds.
Counts stay db-free in this module: the caller derives plain ints
from today's review rows (session.summarize, grade >= 4 pass line)
and passes them in. Explicit non-goals: no confetti or animation
(I-79 owns celebration motion) and no Owned-progress content.
Pure functions, stdlib only (html), no I/O, no DB changes.
"""
from __future__ import annotations

import html as htmlmod

STATUS_ANCHOR = "status-b11-donehero"


def _count(value) -> int:
    """Fail-closed non-negative int coercion; garbage -> 0."""
    try:
        if isinstance(value, bool):
            return 0
        num = int(value)
        return num if num > 0 else 0
    except (TypeError, ValueError):
        return 0
    except Exception:  # noqa: BLE001 — coercion must never raise
        return 0


def _accuracy(value) -> int:
    """Clamp accuracy to 0-100; garbage -> 0."""
    try:
        if isinstance(value, bool):
            return 0
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return 0
    except Exception:  # noqa: BLE001 — coercion must never raise
        return 0


def _due_text(value) -> str:
    """Escaped next-due line; empty input renders an em dash."""
    try:
        if value is None:
            return "\u2014"
        text = value if isinstance(value, str) else str(value)
        text = text.strip()
        return htmlmod.escape(text) if text else "\u2014"
    except Exception:  # noqa: BLE001 — coercion must never raise
        return "\u2014"


def hero_svg() -> str:
    """Calm static all-caught-up illustration; never raises."""
    try:
        return (
            "<svg class='done-hero-art' width='120' height='72' "
            "viewBox='0 0 120 72' fill='none' stroke='currentColor' "
            "stroke-width='3' stroke-linecap='round' "
            "stroke-linejoin='round' role='img' "
            "aria-label='All caught up'>"
            "<title>All caught up</title>"
            "<circle cx='60' cy='26' r='12'/>"
            "<path d='M54 26l5 5 9-11'/>"
            "<path d='M14 52h92'/>"
            "<path d='M24 60h72'/>"
            "<path d='M36 44h48'/>"
            "</svg>"
        )
    except Exception:  # noqa: BLE001 — art must never raise
        return "<svg class='done-hero-art' role='img'></svg>"


def done_hero_html(answered=0, accuracy: int = 0, next_due="") -> str:
    """Full-width session-complete banner; never raises.

    Keeps the Modules-browse and MCP-create next actions so an empty
    queue is a celebration, not a dead end.
    """
    try:
        line = (f"{_count(answered)} answered today · "
                f"{_accuracy(accuracy)}% accuracy · "
                f"next due {_due_text(next_due)}")
        return (
            "<section id='done-hero' class='done-hero'>"
            f"{hero_svg()}"
            "<h2>All caught up.</h2>"
            f"<p>{line}</p>"
            "<p><a href='/modules'>Study the library</a> · "
            "create a module via the MCP tool.</p>"
            "</section>"
        )
    except Exception:  # noqa: BLE001 — renderer must never raise
        return ("<section id='done-hero' class='done-hero'>"
                "<h2>All caught up.</h2></section>")


def hero_css() -> str:
    """Raw banner declarations for the head wire (never <style> tags)."""
    return (
        ".done-hero{max-width:40rem;margin:2rem auto;text-align:center;"
        "padding:2rem 1rem;border-radius:12px}"
        ".done-hero-art{width:120px;height:72px;margin:0 auto}"
        "@media (prefers-reduced-motion:reduce){"
        ".done-hero,.done-hero-art{transition:none}}"
    )


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Session-complete hero "
        "<small>(improvement)</small></h3>"
        "<p>An empty Due queue greets you with a calm all-caught-up "
        "banner — answered today, accuracy, next due — with the "
        "next-action links kept. <code>groundwork/donehero.py</code> "
        "provides <code>done_hero_html()</code> (fail-closed counts, "
        "I-79 confetti-free) and <code>hero_css()</code> (raw "
        "declarations for the head wire).</p>"
        f"{done_hero_html(3, 100, 'tomorrow')}"
    )
