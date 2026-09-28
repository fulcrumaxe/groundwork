"""Conference workshop mode: 2-hour guided module sprints (F-195).

A conference slot runs 2 hours with a facilitator keeping time, so
this module turns the live Due queue into a guided sprint agenda:
cards are budgeted by ``minisession.pick_cards`` (never a copied
cost model), ordered weakest-first (most lapses, frailest memory,
hardest, most overdue), and split into 25-minute segments with
5-minute breaks. Guided mode paces each segment with a client-side
countdown the facilitator calls time on; self mode renders the same
agenda as a work-at-your-own-pace checklist. Sprint length and mode
ride the ``?workshop=`` URL param (``guided``/``self`` plus
30/60/90/120 minutes, default guided 120), so there is no schema
change and no persistence: refresh resets the clocks, never the
queue. Always renders; never raises. The caller is
``Handler.due_html`` beside the focus timer and playlists.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b29-workshop"

SECTION_ANCHOR = "workshop"

SPRINT_MINUTES = 120
BREAK_MINUTES = 5
INTRO_MINUTES = 5

LENGTHS = (30, 60, 90, 120)
MODES = ("guided", "self")
_SELF_ALIASES = ("self", "solo", "selfpaced", "self-paced")


def parse_workshop(value=""):
    """(mode, minutes) for a ``?workshop=`` value; hostile -> guided 120.

    Accepts a bare mode (``guided``, ``self``), a bare length
    (``60``), or ``mode-length`` (``self-90``). Unknown modes and
    off-menu lengths fall back to the default; never raises.
    """
    try:
        raw = str(value or "").strip().lower()
    except Exception:  # noqa: BLE001 -- hostile input takes the default
        return ("guided", SPRINT_MINUTES)
    if not raw:
        return ("guided", SPRINT_MINUTES)
    if raw in MODES or raw in _SELF_ALIASES:
        return ("self" if raw in _SELF_ALIASES else raw, SPRINT_MINUTES)
    if raw.isdigit():
        mins = int(raw)
        return ("guided", mins if mins in LENGTHS else SPRINT_MINUTES)
    head, sep, tail = raw.partition("-")
    if not sep:
        head, sep, tail = raw.partition(":")
    if head in _SELF_ALIASES:
        mode = "self"
    elif head in MODES:
        mode = head
    else:
        return ("guided", SPRINT_MINUTES)
    try:
        mins = int(tail.strip())
    except (TypeError, ValueError):
        return (mode, SPRINT_MINUTES)
    return (mode, mins if mins in LENGTHS else SPRINT_MINUTES)


def _num(card, key, default=0.0) -> float:
    """Float field with a default; hostile cards take the default."""
    try:
        if not isinstance(card, dict):
            return float(default)
        return float(card.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _weak_key(card):
    """Weakest first: lapses, frail stability, difficulty, overdue, id."""
    due = card.get("due") if isinstance(card, dict) else ""
    due = due if isinstance(due, str) and due else "9999"
    cid = card.get("id", "") if isinstance(card, dict) else ""
    return (-_num(card, "lapses"), _num(card, "stability", 1.0),
            -_num(card, "difficulty"), due, str(cid))


def agenda_for(due, workshop="",
               estimate_fn=None,
               new_secs=None, review_secs=None,
               recent=None, tried=None) -> dict:
    """Sprint agenda: mode, minutes, intro flag, weakest-first segments.

    Each segment is {"index", "minutes", "cards", "break_after"} with
    card ids weakest-first; segment 1 holds the weakest cards so the
    room spends its freshest minutes on its hardest recalls. A short
    queue collapses to fewer segments; an empty queue yields none.
    Never raises.
    """
    try:
        from . import minisession as mmod
        mode, minutes = parse_workshop(workshop)
        segs = max(1, minutes // 30)
        intro = minutes > 30
        work = (minutes - (INTRO_MINUTES if intro else 0)
                - (segs - 1) * BREAK_MINUTES)
        try:
            picks = mmod.pick_cards(
                due, minutes=work, estimate_fn=estimate_fn,
                new_secs=mmod.NEW_SECS if new_secs is None else new_secs,
                review_secs=mmod.REVIEW_SECS if review_secs is None else review_secs,
                recent=recent, tried=tried)
        except Exception:  # noqa: BLE001 -- a bad budget empties, not raises
            picks = []
        cards = sorted([c for c in (picks or []) if isinstance(c, dict)],
                       key=_weak_key)
        if not cards:
            return {"mode": mode, "minutes": minutes, "intro": intro,
                    "segments": []}
        segs = min(segs, len(cards))
        seg_mins = max(1, round(work / segs))
        base, extra = divmod(len(cards), segs)
        segments, pos = [], 0
        for s in range(segs):
            n = base + (1 if s < extra else 0)
            chunk = cards[pos:pos + n]
            pos += n
            segments.append({
                "index": s + 1,
                "minutes": seg_mins,
                "cards": [str(c.get("id", "")) for c in chunk],
                "break_after": s < segs - 1,
            })
        return {"mode": mode, "minutes": minutes, "intro": intro,
                "segments": segments}
    except Exception:  # noqa: BLE001 -- agenda must never raise
        return {"mode": "guided", "minutes": SPRINT_MINUTES, "intro": True,
                "segments": []}


def _clock_script() -> str:
    """One shared countdown script for every guided segment clock."""
    return (
        "<script data-workshop>"
        "(function(){try{"
        "var clocks=document.querySelectorAll('.workshop-clock');"
        "Array.prototype.forEach.call(clocks,function(box){"
        "var total=parseInt(box.getAttribute('data-minutes'),10)*60;"
        "var left=total,t=null;"
        "function show(){var m=Math.floor(left/60),s=left%60;"
        "box.textContent=(m<10?'0':'')+m+':'+(s<10?'0':'')+s;}"
        "function tick(){if(left<=0){if(t)clearInterval(t);t=null;"
        "box.textContent='Time \u2014 hand back to the facilitator.';return;}"
        "left--;show();}"
        "var root=box.closest('li')||box.parentNode;"
        "var start=root.querySelector('[data-ws-start]');"
        "var reset=root.querySelector('[data-ws-reset]');"
        "if(start)start.addEventListener('click',function(){"
        "if(t)return;t=setInterval(tick,1000);});"
        "if(reset)reset.addEventListener('click',function(){"
        "if(t)clearInterval(t);t=null;left=total;show();});"
        "show();});}catch(e){}})</script>")


def sprint_html(due, workshop="",
                estimate_fn=None,
                new_secs=None, review_secs=None,
                recent=None, tried=None) -> str:
    """Due-page sprint section: agenda with segments, breaks, clocks.

    Guided mode paces each segment with a countdown the facilitator
    calls time on; self mode renders the same agenda as a checklist.
    Empty queue renders the calm all-clear with no buttons so the
    ``workshop`` anchor never moves. Never raises.
    """
    try:
        agenda = agenda_for(due, workshop, estimate_fn,
                            new_secs, review_secs, recent, tried)
        mode, minutes = agenda["mode"], agenda["minutes"]
        segments = agenda["segments"]
        if not segments:
            return (f"<section id='{SECTION_ANCHOR}'><h2>Workshop sprint</h2>"
                    "<p>All clear \u2014 nothing due. A sprint needs a queue; "
                    "browse a module to learn ahead.</p></section>")
        n = len(segments)
        pace = ("the facilitator calls time on each segment"
                if mode == "guided" else
                "work at your own pace and tick segments off as you finish")
        parts = [f"<section id='{SECTION_ANCHOR}'><h2>Workshop sprint</h2>",
                 f"<p>{minutes}-minute {mode} sprint \u2014 {pace}.</p>"]
        if agenda["intro"]:
            parts.append("<p>Minutes 0-5: the facilitator frames the goal; "
                         "then segments run weakest-first.</p>")
        parts.append("<p><a href='#up-next'>Start the sprint</a>.</p><ol>")
        for seg in segments:
            ids = [c for c in seg["cards"] if c]
            shown = ", ".join(ids[:6]) + ("..." if len(ids) > 6 else "")
            noun = "card" if len(ids) == 1 else "cards"
            line = (f"Segment {seg['index']} of {n} (~{seg['minutes']} min): "
                    f"{len(ids)} {noun} weakest-first ({shown}).")
            parts.append(f"<li>{html.escape(line)}")
            if mode == "guided":
                parts.append(
                    f" <span class='workshop-clock' data-minutes='{seg['minutes']}'>"
                    f"{seg['minutes']}:00</span> "
                    "<button type='button' data-ws-start>Start</button> "
                    "<button type='button' data-ws-reset>Reset</button>")
            parts.append("</li>")
            if seg["break_after"]:
                parts.append("<li><small>Break \u2014 "
                             f"{BREAK_MINUTES} minutes.</small></li>")
        parts.append("</ol>")
        if mode == "guided":
            parts.append(_clock_script())
        parts.append(
            "<p><small>Sprint: "
            "<a href='/due?workshop=guided-120'>guided 2h</a> \u00b7 "
            "<a href='/due?workshop=self-120'>self-paced 2h</a> \u00b7 "
            "<a href='/due?workshop=guided-60'>guided 1h</a> \u00b7 "
            "<a href='/due?workshop=self-60'>self-paced 1h</a>"
            "</small></p></section>")
        return "".join(parts)
    except Exception:  # noqa: BLE001 -- section must always render
        return (f"<section id='{SECTION_ANCHOR}'><h2>Workshop sprint</h2>"
                "<p>Sprint agenda temporarily unavailable.</p></section>")


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch29.py."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Conference workshop "
            "<small>(feature)</small></h3>"
            "<p>A 2-hour guided sprint \u2014 "
            "<code>groundwork/workshop.py</code> budgets the live Due "
            "queue via <code>minisession.pick_cards()</code> (no copied "
            "cost model), orders cards weakest-first into 25-minute "
            "segments with 5-minute breaks, and paces guided mode with "
            "facilitator-called countdowns; mode and length ride "
            "<code>?workshop=</code> with no schema change.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Conference workshop</h3>"
                "<p>Workshop help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "conference-workshop",
        "kind": "feature",
        "title": "Conference workshop",
        "blurb": ("A 2-hour guided sprint from your queue \u2014 "
                  "weakest-first segments with breaks, timed or self-paced."),
        "path": "/due",
        "anchor": SECTION_ANCHOR,
    }
