"""Ask-for-a-nudge button: reveal the next hint tier freely (I-188).

Progressive reveal (cards.hints_html -> hinttiers.hints_html) shows
only the 1+attempts prefix of a card's hints: a stuck learner on
attempt zero must submit a wrong answer just to unlock the next
tier. This module appends one client-side button after the shown
tiers that reveals the next withheld tier per click -- no POST, no
grade, no scheduling change, no schema change.

The withheld tiers ride along as hidden tiered disclosures reusing
the hinttiers vocabulary (tier_class/tier_label), so styling stays
single-sourced; a small guarded script unhides one per click and
retires the button when none remain. When every tier is already
shown (or the card has no hints) button_html returns "", leaving
legacy output byte-identical. Pure functions, stdlib only (html),
never raises.
"""
from __future__ import annotations

import html as htmlmod

from . import hinttiers as hinttiersmod

STATUS_ANCHOR = "status-b28-asknudge"

BUTTON_LABEL = "Ask for a nudge"
SPENT_LABEL = "No more hints"

_SCRIPT = (
    "<script>if(!window.__asknudge){window.__asknudge=true;"
    "document.addEventListener('click',function(e){"
    "var b=e.target.closest('.asknudge-btn');if(!b||b.disabled)return;"
    "var w=b.closest('.asknudge');if(!w)return;"
    "var nx=w.querySelector('details[hidden]');"
    "if(!nx){b.disabled=true;b.textContent='No more hints';return;}"
    "nx.removeAttribute('hidden');"
    "var left=w.querySelectorAll('details[hidden]').length;"
    "if(left>0){b.textContent='Ask for a nudge ('+left+' left)';}"
    "else{b.textContent='No more hints';b.disabled=true;}});}</script>"
)


def _as_list(hints) -> list:
    """Stored hints as a list; hostile input fails closed to []."""
    try:
        if isinstance(hints, (list, tuple)):
            return list(hints)
    except Exception:  # noqa: BLE001 -- coercion must never raise
        pass
    return []


def _is_blank(value) -> bool:
    """True when a hint carries no visible text; hostile -> blank."""
    try:
        text = value if isinstance(value, str) else str(value)
    except Exception:  # noqa: BLE001 -- probe must never raise
        return True
    return not text.strip()


def shown_count(attempts) -> int:
    """Tiers the server already reveals: 1+attempts, minimum 0.

    Hostile input (bool, text, None) fails closed to 1, mirroring
    the hinttiers prefix default. Never raises.
    """
    try:
        if isinstance(attempts, bool):
            return 1
        return max(0, 1 + int(attempts))
    except (TypeError, ValueError):
        return 1
    except Exception:  # noqa: BLE001 -- count must never raise
        return 1


def hidden_count(hints, attempts: int = 0) -> int:
    """Withheld tiers the button could still reveal; never negative."""
    try:
        return max(0, len(_as_list(hints)) - shown_count(attempts))
    except Exception:  # noqa: BLE001 -- count must never raise
        return 0


def next_tier_label(hints, attempts: int = 0) -> str:
    """Human label of the next withheld tier; "" when none remain."""
    try:
        items = _as_list(hints)
        idx = shown_count(attempts)
        if idx < 0 or idx >= len(items):
            return ""
        return hinttiersmod.tier_label(idx)
    except Exception:  # noqa: BLE001 -- label must never raise
        return ""


def button_html(hints, attempts: int = 0) -> str:
    """Nudge button plus hidden tiers; "" when none remain (legacy).

    Blank withheld hints are skipped so every click reveals real
    content; tier classes/labels reuse hinttiers by original index.
    Never raises.
    """
    try:
        items = _as_list(hints)
        start = shown_count(attempts)
        rest = [(i, items[i])
                for i in range(max(0, start), len(items))
                if not _is_blank(items[i])]
        if not rest:
            return ""
        parts = ["<span class='asknudge'>",
                 f"<button type='button' class='asknudge-btn'>"
                 f"{BUTTON_LABEL} ({len(rest)} left)</button>"]
        for i, hint in rest:
            body = hint if isinstance(hint, str) else str(hint)
            parts.append(
                f"<details class='{hinttiersmod.tier_class(i)}' hidden>"
                f"<summary><span class='hint-tag'>"
                f"{hinttiersmod.tier_label(i)}</span></summary>"
                f"{htmlmod.escape(body)}</details>")
        parts.append("</span>")
        parts.append(_SCRIPT)
        return "".join(parts)
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def tour_entry() -> dict:
    """Tour registry entry for the nudge button."""
    return {"id": "ask-nudge", "kind": "improvement",
            "title": "Ask for a nudge",
            "blurb": ("Stuck before attempt one? One click reveals the "
                      "next hint tier -- no wrong answer required."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch28.py."""
    try:
        return (f"<h3 id='{STATUS_ANCHOR}'>Ask for a nudge "
                "<small>(improvement)</small></h3>"
                "<p>Stuck on attempt zero? An <b>Ask for a nudge</b> "
                "button now rides after the shown hint tiers "
                "(<code>cards.hints_html</code>): each click reveals "
                "the next withheld tier -- nudge, pointer, worked "
                "step -- with no POST, no grade, and no scheduling "
                "change. Withheld tiers reuse the "
                "<code>hinttiers</code> classes, and cards with "
                "nothing left to reveal render exactly as before.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Ask for a nudge</h3>"
                "<p>Help unavailable.</p>")
