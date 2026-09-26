"""Session playlists: one-click 5/10/20-minute mixes (F-120).

Three rows, one per mix length, each budgeted from the live Due queue
by ``minisession.pick_cards`` — playlists never copy the cost model or
the greedy fill loop. Pure functions, stdlib only, no I/O, no
persistence. Always renders; never raises. The caller is
``Handler.due_html`` beside the session box and focus timer.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b24-playlists"

SECTION_ANCHOR = "playlists"

MIX_MINUTES = (5, 10, 20)


def _lengths(minutes_list) -> list:
    """Validated mix lengths; hostile input falls back to MIX_MINUTES."""
    try:
        lengths = [int(m) for m in (minutes_list or ())]
    except (TypeError, ValueError):
        return list(MIX_MINUTES)
    lengths = [m for m in lengths if m > 0]
    return lengths or list(MIX_MINUTES)


def _picks_for(due, minutes_list=MIX_MINUTES, estimate_fn=None,
               new_secs=None, review_secs=None,
               recent=None, tried=None) -> dict:
    """Minutes -> picked card dicts, via minisession budgeting."""
    from . import minisession as mmod
    out: dict = {}
    for mins in _lengths(minutes_list):
        try:
            out[mins] = mmod.pick_cards(
                due, minutes=mins, estimate_fn=estimate_fn,
                new_secs=mmod.NEW_SECS if new_secs is None else new_secs,
                review_secs=mmod.REVIEW_SECS if review_secs is None else review_secs,
                recent=recent, tried=tried)
        except Exception:  # noqa: BLE001 -- one bad mix never breaks the rest
            out[mins] = []
    return out


def mixes_for(due, minutes_list=MIX_MINUTES, estimate_fn=None,
              new_secs=None, review_secs=None,
              recent=None, tried=None) -> dict:
    """Minutes -> picked card ids for each mix; {} only when hostile.

    Empty queue yields every length mapped to []. Never raises.
    """
    try:
        picks = _picks_for(due, minutes_list, estimate_fn,
                           new_secs, review_secs, recent, tried)
        return {m: [str(c.get("id", "")) for c in cards if isinstance(c, dict)]
                for m, cards in picks.items()}
    except Exception:  # noqa: BLE001 -- mixes must never raise
        return {}


def playlist_html(due, minutes_list=MIX_MINUTES, estimate_fn=None,
                  new_secs=None, review_secs=None,
                  recent=None, tried=None) -> str:
    """Due-page section: one start row per mix length.

    Non-empty queue always yields every row (pick_cards guarantees >= 1
    card); empty queue renders the calm all-clear with no buttons so the
    ``playlists`` anchor never moves. Never raises.
    """
    try:
        from . import minisession as mmod
        picks = _picks_for(due, minutes_list, estimate_fn,
                           new_secs, review_secs, recent, tried)
        rows = [(m, [c for c in cards if isinstance(c, dict)])
                for m, cards in picks.items()]
        if not any(cards for _, cards in rows):
            return (f"<section id='{SECTION_ANCHOR}'><h2>Session playlists</h2>"
                    "<p>All clear — nothing due. Browse a module to learn ahead.</p></section>")
        parts = [f"<section id='{SECTION_ANCHOR}'><h2>Session playlists</h2>"]
        for mins, cards in rows:
            if not cards:
                continue
            secs = mmod.planned_seconds(cards, estimate_fn, mmod.NEW_SECS
                                        if new_secs is None else new_secs,
                                        mmod.REVIEW_SECS if review_secs is None else review_secs)
            about = max(1, round(secs / 60.0))
            n = len(cards)
            noun = "card" if n == 1 else "cards"
            parts.append(
                f"<p>{html.escape(str(n))} {noun}, ~{about} min. "
                f"<a href='#up-next'>Start {mins}-minute mix</a>.</p>")
        parts.append("</section>")
        return "".join(parts)
    except Exception:  # noqa: BLE001 -- section must always render
        return (f"<section id='{SECTION_ANCHOR}'><h2>Session playlists</h2>"
                "<p>Playlists temporarily unavailable.</p></section>")


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch24.py."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Session playlists "
            "<small>(feature)</small></h3>"
            "<p>One click starts a 5, 10, or 20-minute mix — "
            "<code>groundwork/playlists.py</code> budgets each mix from "
            "the head of the Due queue via "
            "<code>minisession.pick_cards()</code> (no copied cost model) "
            "and renders a start row per length, all-clear when nothing "
            "is due.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Session playlists</h3>"
                "<p>Playlist help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "session-playlists",
        "kind": "feature",
        "title": "Session playlists",
        "blurb": ("Pick your minutes — 5, 10, or 20 — and start a mix "
                  "built from your queue."),
        "path": "/due",
        "anchor": SECTION_ANCHOR,
    }
