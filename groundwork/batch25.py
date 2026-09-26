"""Batch 25 home: one anchored subsection per shipped item.

Improvements I-162–I-169 make cards tactile (touch + keyboard
Parsons reorder, partial-order checks, click-to-pair matching,
pre-filled trace tables with per-cell feedback, predict-output
3-strike retries, live rubric checklists, line-comment code review,
side-by-side compare panes). Features F-129–F-136 widen the circle
and the horizon (team challenges, classroom quests, seasonal
Owntober goals, anniversary recaps, ship-it confidence, interview
recap tracks, onboarding countdowns, rabbit-hole free explore).

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): sixteen section imports plus the join would
overflow it. Each section still renders from its own area module
(never web.py); this module only joins them. Wired into the Status
page by status.page_html next to batch24_html.
"""
from __future__ import annotations

from . import anniversary as anniversarymod
from . import classquests as classquestsmod
from . import comparesplit as comparesplitmod
from . import interviewprep as interviewprepmod
from . import linecomment as linecommentmod
from . import matchpair as matchpairmod
from . import onboard as onboardmod
from . import parcheck as parcheckmod
from . import parkeys as parkeysmod
from . import predtry as predtrymod
from . import rabbithole as rabbitholemod
from . import rubriclive as rubriclivemod
from . import seasonevent as seasoneventmod
from . import shipconf as shipconfmod
from . import teamchallenge as teamchallengemod
from . import tracetable as tracetablemod


def batch25_html(db_path: str = "") -> str:
    """Batch 25 home: one anchored subsection per shipped item.

    Improvements first, then the features — the same shape as
    batch24_html. Sections render from their own area modules;
    db_path is accepted for call-site shape and ignored.
    """
    _ = db_path
    return "".join([
        "<h2 id='status-batch25'>Batch 25: tactile cards, wider circle</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. Cards turn tactile — touch and "
        "keyboard Parsons, partial-order checks, tap-to-pair matching, "
        "pre-filled trace tables, 3-strike predict retries, live "
        "rubric checklists, line-comment review, side-by-side compare "
        "panes; the circle widens — team challenges, classroom quests, "
        "a seasonal Owntober goal, anniversary recaps, ship-it "
        "confidence, interview recap tracks, onboarding countdowns, "
        "and rabbit-hole free explore.</p>",
        parkeysmod.section_html(),
        parcheckmod.section_html(),
        matchpairmod.section_html(),
        tracetablemod.section_html(),
        predtrymod.section_html(),
        rubriclivemod.section_html(),
        linecommentmod.section_html(),
        comparesplitmod.section_html(),
        teamchallengemod.status_section_html(),
        classquestsmod.section_html(),
        seasoneventmod.status_section_html(),
        anniversarymod.section_html(),
        shipconfmod.status_section_html(),
        interviewprepmod.section_html(),
        onboardmod.section_html(),
        rabbitholemod.section_html(),
    ])
