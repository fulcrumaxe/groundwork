"""Loading skeletons for module pages (I-81).

Module pages build mid-request in ``Handler.module_html`` (groundwork/web.py):
seven DB reads (module, cards, concepts, attempts, history, owned, ladders,
plus decisions/clarity/known lookups) followed by the per-concept lesson
render loop. While that work runs the browser shows nothing. This module
provides an instant static shell mirroring the real structure — title bar,
progress bar on the existing ``.bar``/``i`` selectors, and N lesson rows —
so the parent can flush it first and swap in real content when generation
finishes.

Static two-tone placeholders only: no shimmer slide (the motion budget caps
total animation at 300ms per I-98; a ``background-position`` sweep needs
~1.2s to read well). One optional opacity pulse (250ms) applies only under
``prefers-reduced-motion:no-preference``; reduced-motion users always see
the static shell. Tones reuse the site tokens (``var(--paper)`` shell, track
tone matching the existing ``.bar`` track) instead of new hex literals.
``skeletons_css()`` returns raw declarations only, never ``<style>`` tags —
the parent concatenates it into the head wire next to ``progbar_css()``.
Accessibility: the shell carries no readable text (empty spans only); the
outer wrapper sets ``aria-busy="true"`` while the inner placeholders are
``aria-hidden="true"``, so assistive tech never announces fake lessons.
Pure functions, stdlib only, no groundwork imports, no DB/schema changes,
fail closed (never raise).
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b12-skeletons"

DEFAULT_ROWS = 3
MAX_ROWS = 8
PULSE_MS = 250
MAX_DURATION_MS = 300


def _rows(value=DEFAULT_ROWS) -> int:
    """Clamp a row count to 1..MAX_ROWS; garbage fails closed to DEFAULT_ROWS."""
    try:
        if isinstance(value, bool):
            return DEFAULT_ROWS
        num = int(value)
        if num < 1 or num > MAX_ROWS:
            return DEFAULT_ROWS
        return num
    except Exception:  # noqa: BLE001 — row lookup must never raise
        return DEFAULT_ROWS


def skeleton_html(rows=DEFAULT_ROWS) -> str:
    """Placeholder shell mirroring module-page structure; never raises.

    Title bar, progress bar (real ``.bar`` selectors), then ``rows`` lesson
    rows (heading line, sub line, status-chip pill). All placeholders are
    empty spans — no fake text for AT to read. Outer wrapper carries
    ``aria-busy``; inner shell is ``aria-hidden``.
    """
    try:
        count = _rows(rows)
        lesson_rows = "".join(
            "<section class='sk-row'>"
            "<span class='sk-line [REDACTED]'></span>"
            "<span class='sk-line sk-row-sub'></span>"
            "<span class='sk-chip'></span>"
            "</section>"
            for _ in range(count)
        )
        return (
            "<div class='sk' aria-busy='true' "
            "aria-label='Loading module content'>"
            "<div class='sk-inner' aria-hidden='true'>"
            "<div class='[REDACTED]'>"
            "<span class='sk-line sk-title'></span>"
            "<span class='sk-line sk-sub'></span>"
            "</div>"
            "<div class='bar [REDACTED]'><i></i></div>"
            + lesson_rows +
            "</div></div>"
        )
    except Exception:  # noqa: BLE001 — placeholder must never raise
        return (
            "<div class='sk' aria-busy='true' "
            "aria-label='Loading module content'>"
            "<div class='sk-inner' aria-hidden='true'></div></div>"
        )


def skeletons_css() -> str:
    """Raw CSS declarations for the skeleton shell; never raises.

    Static two-tone base (no animation at all); one 250ms opacity pulse
    applies only under ``prefers-reduced-motion:no-preference``. Raw
    declarations only — no wrapping tags.
    """
    try:
        return (
            ".sk{background:var(--paper);border-radius:10px}"
            ".sk-line{display:block;background:#e6e6e6;border-radius:4px;"
            "min-height:.9rem;margin:.4rem 0}"
            ".sk-title{min-height:1.4rem;max-width:60%}"
            ".sk-sub{max-width:85%}"
            ".[REDACTED]{background:#e6e6e6}"
            ".[REDACTED] i{display:block;width:40%;background:#cfcfcf;"
            "min-height:.5rem;border-radius:4px}"
            ".sk-row{border:1px solid #ddd;border-radius:10px;"
            "padding:.75rem 1rem;margin:.75rem 0}"
            ".[REDACTED]{max-width:45%}"
            ".sk-row-sub{max-width:70%}"
            ".sk-chip{display:inline-block;width:4rem;min-height:1.1rem;"
            "background:#e6e6e6;border-radius:999px}"
            "@media(prefers-reduced-motion:no-preference){"
            ".sk-line,.sk-chip,.[REDACTED] i{"
            f"animation:gw-sk-pulse {PULSE_MS}ms ease-in-out infinite alternate}}"
            "@keyframes gw-sk-pulse{from{opacity:1}to{opacity:.55}}"
        )
    except Exception:  # noqa: BLE001 — CSS builder must never raise
        return ".sk{background:var(--paper)}"


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Loading skeletons "
            "<small>(improvement)</small></h3>"
            "<p>Module pages show an instant static shell while lessons "
            "generate: a title bar, the progress bar on the existing "
            "<code>.bar</code> selectors, and placeholder lesson rows — "
            "empty spans only, so screen readers hear nothing fake (outer "
            "wrapper <code>aria-busy</code>, inner shell "
            "<code>aria-hidden</code>). Static two-tone placeholders with "
            "one optional 250ms opacity pulse gated behind "
            "<code>prefers-reduced-motion:no-preference</code>, inside the "
            "300ms motion budget. <code>groundwork/skeletons.py</code> "
            "provides <code>skeleton_html()</code> and "
            "<code>skeletons_css()</code> (raw declarations only, no "
            "<code>&lt;style&gt;</code> tags — the parent concatenates it "
            "into the head wire); helpers fail closed, never raise.</p>"
        )
    except Exception:  # noqa: BLE001 — status must never raise
        return f"<h3 id='{STATUS_ANCHOR}'>Loading skeletons</h3>"


def tour_entry() -> dict:
    """Registry entry shape for tour.ENTRIES; the parent copies it in."""
    return {
        "id": "loading-skeletons",
        "kind": "improvement",
        "title": "Loading skeletons",
        "blurb": "Module pages show a static placeholder shell — title, progress, lesson rows — while lessons generate.",
        "path": "/status",
        "anchor": "status-b12-skeletons",
    }
