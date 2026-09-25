"""Focus timer with queue auto-fill (F-119).

One click starts a 25-minute focus block whose card list
auto-fills from the head of today's Due queue (three minutes a
card, at least one); the countdown runs client-side and the
session suggestion follows the live queue — clear the queue and
the timer says the block is free. Short and long breaks
round it out. No accounts, no history writes, no persistence:
refresh resets the clock, never the queue. Always renders;
never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b23-focustimer"

SECTION_ANCHOR = "focus-timer"

WORK_MINUTES = 25
SHORT_MINUTES = 5
LONG_MINUTES = 15
SECS_PER_CARD = 180


def mix_for(due, minutes: int = WORK_MINUTES) -> list:
    """Head-of-queue card ids filling one block; [] when empty."""
    try:
        rows = [c for c in (due or []) if isinstance(c, dict)]
        if not rows:
            return []
        try:
            mins = int(minutes)
        except (TypeError, ValueError):
            mins = WORK_MINUTES
        count = max(1, (mins * 60) // SECS_PER_CARD)
        return [str(c.get("id", "")) for c in rows[:count]]
    except Exception:  # noqa: BLE001 -- mix must never raise
        return []


def timer_html(due, minutes: int = WORK_MINUTES) -> str:
    """Focus block with countdown; queue-clear note when empty."""
    try:
        mix = mix_for(due, minutes)
        try:
            mins = int(minutes)
        except (TypeError, ValueError):
            mins = WORK_MINUTES
        if not mix:
            return (f"<div id='{SECTION_ANCHOR}'><h2>Focus timer</h2>"
                    "<p>Queue clear — the next block is free time.</p></div>")
        covers = (f"this {mins}-minute block covers "
                  f"{len(mix)} card{'s' if len(mix) != 1 else ''}")
        return (
            f"<div id='{SECTION_ANCHOR}'><h2>Focus timer</h2>"
            f"<p>{html.escape(covers)} "
            f"({html.escape(', '.join(mix[:8]))}"
            f"{'…' if len(mix) > 8 else ''}).</p>"
            f"<p><span class='focus-clock' data-minutes='{mins}'>"
            f"{mins}:00</span> "
            f"<button type='button' data-focus-start>Start</button> "
            f"<button type='button' data-focus-reset>Reset</button></p>"
            f"<p><small>Breaks: {SHORT_MINUTES} min short, "
            f"{LONG_MINUTES} min every fourth block.</small></p>"
            "<script data-focustimer>"
            "(function(){try{"
            "var box=document.querySelector('.focus-clock');"
            "if(!box)return;"
            "var total=parseInt(box.getAttribute('data-minutes'),10)*60;"
            "var left=total,t=null;"
            "function show(){var m=Math.floor(left/60),s=left%60;"
            "box.textContent=(m<10?'0':'')+m+':'+(s<10?'0':'')+s;}"
            "function tick(){if(left<=0){clearInterval(t);t=null;"
            "box.textContent='Done — take a break.';return;}"
            "left--;show();}"
            "var root=box.parentNode.parentNode;"
            "var start=root.querySelector('[data-focus-start]');"
            "var reset=root.querySelector('[data-focus-reset]');"
            "if(start)start.addEventListener('click',function(){"
            "if(t)return;t=setInterval(tick,1000);});"
            "if(reset)reset.addEventListener('click',function(){"
            "if(t)clearInterval(t);t=null;left=total;show();});"
            "show();}catch(e){}})</script></div>")
    except Exception:  # noqa: BLE001 -- timer must never raise
        return (f"<div id='{SECTION_ANCHOR}'><h2>Focus timer</h2>"
                "<p>Timer temporarily unavailable.</p></div>")


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Focus timer "
            "<small>(feature)</small></h3>"
            "<p>Twenty-five minutes, cards included — "
            "<code>groundwork/focustimer.py</code> auto-fills each "
            "focus block from the head of the Due queue with a "
            "client-side countdown (no persistence, refresh resets "
            "the clock, never the queue).</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Focus timer</h3>"
                "<p>Timer help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "focus-timer",
        "kind": "feature",
        "title": "Focus timer",
        "blurb": ("A 25-minute block auto-filled from your queue — "
                  "start, practice, break."),
        "path": "/due",
        "anchor": SECTION_ANCHOR,
    }
