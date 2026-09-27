"""Batch 26 home: one anchored subsection per shipped item.

Improvements I-170–I-177 sharpen the drills where learners meet
them (live extend-feature param checklists, rebuild spec beside
the editor, refactor behavior-diffs on measured samples,
click-to-order call-path chips, clickable blast-radius graphs,
odd-one-out strike-through elimination, decision quotes beside
rationale choices, CSS flashcard flips). Features F-138–F-144 plus
F-148 keep motivation honest (why-am-I-seeing-this on every
recommendation, granular opt-outs, plain mode, kids mode, quiet
motion-free celebrations, plain milestone copy, thank-the-author
notes, the free-forever spotlight). F-137 was already shipped as
serendipity.py, so it joins as a cross-off, not a new section.

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): sixteen section imports plus the join would
overflow it. Each section still renders from its own area module
(never web.py); this module only joins them. Wired into the Status
page by status.page_html next to batch25_html.
"""
from __future__ import annotations

from . import behavdiff as behavdiffmod
from . import blastgraph as blastgraphmod
from . import callchips as callchipsmod
from . import calmjoy as calmjoymod
from . import cardflip as cardflipmod
from . import extlive as extlivemod
from . import freeedu as freeedumod
from . import kids as kidsmod
from . import optout as optoutmod
from . import plain as plainmod
from . import plaincopy as plaincopymod
from . import ratquote as ratquotemod
from . import specsplit as specsplitmod
from . import thanks as thanksmod
from . import whysee as whyseemod
from . import xout as xoutmod


def batch26_html(db_path: str = "") -> str:
    """Batch 26 home: one anchored subsection per shipped item.

    Improvements first, then the features — the same shape as
    batch25_html. Sections render from their own area modules;
    db_path is accepted for call-site shape and ignored.
    """
    _ = db_path
    return "".join([
        "<h2 id='status-batch26'>Batch 26: sharper drills, honest motivation</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. Drills get sharper — live param "
        "checklists, spec beside the editor, measured behavior-diffs, "
        "click-to-order chips, clickable dependency graphs, "
        "strike-through elimination, decision quotes, card flips; "
        "motivation stays honest — every recommendation says why, "
        "any element opts out alone, plain and kids modes, quiet "
        "celebrations, plain milestone copy, thank-the-author notes, "
        "and the free-forever spotlight.</p>",
        extlivemod.section_html(),
        specsplitmod.section_html(),
        behavdiffmod.section_html(),
        callchipsmod.section_html(),
        blastgraphmod.section_html(),
        xoutmod.section_html(),
        ratquotemod.section_html(),
        cardflipmod.section_html(),
        whyseemod.section_html(),
        optoutmod.section_html(),
        plainmod.section_html(),
        kidsmod.section_html(),
        calmjoymod.status_section_html(),
        plaincopymod.section_html(),
        thanksmod.section_html(),
        freeedumod.section_html(),
    ])
