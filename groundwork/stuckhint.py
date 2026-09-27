"""Hint tiers unlock by attempts AND time stuck (I-187).

Card hints used to unlock on attempts alone: hinttiers.hints_html
reveals a 1+attempts prefix, so a quietly struggling learner earns
nothing without spending a failed submit. This module adds the time
half: one extra tier unlocks once stuck time sits inside
[STUCK_SECONDS, STUCK_WINDOW_S] (2 to 10 minutes). Past the window
the gap reads as a session break -- a fresh return, not stuck time
(flowdetect GAP_CAP_S precedent).

Two honest time sources, no schema change. Server-side,
stuck_seconds_since() measures seconds from the last attempt stamp
(reviews.reviewed_at, already stored) to now for the re-render path.
Client-side, hints_html() ships the next locked tier hidden plus a
small timer script, because no per-card open-timestamp substrate
exists server-side: dwell on the open card is only measurable in
the browser (tabmemory localStorage-script precedent).

Caller path (real learner path, never a Status demo):
cards.hints_html delegates here; Due and module pages inherit it
through cards.answer_widget with no web.py change. Tier vocabulary
and classes stay single-sourced in hinttiers (this module renders
through hinttiers.hint_html -- no parallel engine).

Legacy fallback: stuck_seconds=None (or unparseable, or outside
the window) renders the attempts prefix exactly as hinttiers does;
timer=False, empty hints, and fully-visible tiers are byte-identical
to hinttiers.hints_html. No-JS readers see the same visible tiers
(the hidden tier stays hidden). Pure functions, stdlib only
(datetime) plus the hinttiers sibling import; never raises.
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import hinttiers as hinttiersmod

STATUS_ANCHOR = "status-b28-stuckhint"

#: Stuck seconds before the next tier unlocks.
STUCK_SECONDS = 120

#: Gaps past this are session breaks, not stuck time.
STUCK_WINDOW_S = 600


def _parse_ts(value):
    """ISO-ish stamp or datetime -> aware UTC datetime; else None."""
    try:
        if isinstance(value, datetime):
            dt = value
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
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


def stuck_seconds_since(last_iso, now=None) -> float | None:
    """Seconds from the last attempt stamp to now; None when unknown.

    `now` accepts a datetime, an ISO string, or None (this instant).
    Future stamps clamp to 0.0 (just answered, not stuck); anything
    unparseable yields None so the caller keeps the legacy prefix.
    """
    try:
        at = _parse_ts(last_iso)
        if at is None:
            return None
        moment = _parse_ts(now) if now is not None else None
        if moment is None and now is None:
            try:
                moment = datetime.now(timezone.utc)
            except Exception:  # noqa: BLE001 -- clock never breaks render
                return None
        if moment is None:
            return None
        return max(0.0, (moment - at).total_seconds())
    except Exception:  # noqa: BLE001 -- measurement never raises
        return None


def is_stuck(stuck_seconds) -> bool:
    """True when stuck time earns a tier: inside [120, 600] seconds."""
    try:
        secs = float(stuck_seconds)
        if secs != secs:  # NaN fails closed
            return False
        return STUCK_SECONDS <= secs <= STUCK_WINDOW_S
    except (TypeError, ValueError):
        return False


def stuck_bonus(stuck_seconds) -> int:
    """Extra tiers earned by stuck time: 1 when stuck, else 0."""
    try:
        return 1 if is_stuck(stuck_seconds) else 0
    except Exception:  # noqa: BLE001 -- bonus never raises
        return 0


def _attempt_count(attempts) -> int:
    """Coerce attempts exactly like hinttiers.hints_html does."""
    try:
        return int(attempts)
    except (TypeError, ValueError):
        return 0


def visible_count(total, attempts, stuck_seconds=None) -> int:
    """Tiers to show: 1 + attempts + stuck bonus, clamped to total."""
    try:
        try:
            size = int(total)
        except (TypeError, ValueError):
            return 0
        if size <= 0:
            return 0
        count = 1 + _attempt_count(attempts) + stuck_bonus(stuck_seconds)
        return max(0, min(size, count))
    except Exception:  # noqa: BLE001 -- counting never raises
        return 0


def remaining_seconds(stuck_seconds) -> int:
    """Client wait before the timer unlocks the next tier.

    Partially-stuck learners (60s in) wait only the remainder; unknown
    or fresh learners wait the full threshold. Always >= 1.
    """
    try:
        secs = float(stuck_seconds)
        if secs != secs or secs < 0 or secs >= STUCK_SECONDS:
            return STUCK_SECONDS
        return max(1, int(STUCK_SECONDS - secs))
    except (TypeError, ValueError):
        return STUCK_SECONDS


def timer_js() -> str:
    """Inline script: reveal this card's hidden tier after its wait.

    Per-card self-targeting via document.currentScript (no global
    guard, so every Due card arms its own timer); the wait reads from
    the sibling data-stuck-secs attribute, falling back to 120
    (mirrors STUCK_SECONDS). Fail-closed try/catch; no-JS keeps the
    legacy visible tiers.
    """
    return (
        "<script>(function(){try{"
        "var s=document.currentScript;var box=s.parentNode;"
        "var d=box.querySelector('[data-stuck-next]');if(!d)return;"
        "var secs=parseInt(d.getAttribute('data-stuck-secs'),10);"
        "if(!(secs>0))secs=120;"
        "setTimeout(function(){d.removeAttribute('hidden');"
        "var n=box.querySelector('.stuck-note');"
        "if(n)n.textContent='Stuck time earned this hint - take a look.';"
        "},secs*1000);}catch(e){}})();</script>"
    )


def hints_html(hints, attempts: int = 0, stuck_seconds=None,
               timer: bool = True) -> str:
    """Stuck-aware tiered reveal; legacy bytes when nothing is locked.

    The visible prefix holds visible_count() tiers rendered through
    hinttiers.hint_html (same nudge/pointer/worked classes, same
    id='hints' wrapper). When a further tier exists and timer is on,
    it rides along hidden with a note plus timer_js(); otherwise --
    timer=False, empty hints, or everything visible -- output equals
    hinttiers.hints_html for the same prefix, byte for byte.
    """
    try:
        if not isinstance(hints, (list, tuple)) or not hints:
            return ""
        items = list(hints)
        total = len(items)
        shown = visible_count(total, attempts, stuck_seconds)
        if shown <= 0:
            return ""
        if shown >= total or not timer:
            return hinttiersmod.hints_html(items, shown - 1)
        body = "".join(
            hinttiersmod.hint_html(h, i, total)
            for i, h in enumerate(items[:shown]))
        wait = remaining_seconds(stuck_seconds)
        nxt = hinttiersmod.hint_html(items[shown], shown, total)
        return (
            "<div id='hints'>" + body
            + f"<div hidden data-stuck-next data-stuck-secs='{wait}'>"
            + nxt + "</div>"
            + "<small class='stuck-note'>Stuck? The next hint opens "
            f"on its own in about {wait}s.</small>"
            + timer_js() + "</div>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch28.py."""
    try:
        sample = hints_html(
            ["Try the base case first", "Trace n=1 by hand"], 0, 150,
            timer=False)
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Stuck-time hint unlock "
            "<small>(improvement)</small></h3>"
            "<p>Hint tiers unlock by attempts <i>and</i> time stuck: "
            "<code>groundwork/stuckhint.py</code> adds one tier once "
            "stuck time sits between 2 and 10 minutes "
            "(<code>visible_count()</code>), served on the card path "
            "(<code>cards.hints_html</code>) with tier styling still "
            "owned by <code>hinttiers</code>. Gaps past 10 minutes "
            "read as session breaks, and a client-side timer reveals "
            "the next locked tier on the open card -- no schema "
            "change, no new exercise types. A stuck sample (both "
            "tiers visible) renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Stuck-time hint unlock</h3>"
                "<p>Hint help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "stuck-hints",
        "kind": "improvement",
        "title": "Hints unlock with time stuck",
        "blurb": ("Stuck 2 minutes with no new attempt? The next hint "
                  "tier opens on its own."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
