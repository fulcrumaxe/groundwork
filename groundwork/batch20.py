"""Batch 20 home: one anchored subsection per shipped item.

Improvements I-116, I-117, I-119, I-121–I-125 deepen lessons
(version diffs, pins, handouts, tab memory, calibration levels,
extremes, peer hints, visual gates). Features F-85–F-92 add two new
Due-queue exercise types (89-90) plus kata libraries, reading groups,
spaced re-teaching, a personal forgetting curve, and peak-time
suggestions.

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): seventeen section imports plus the join would overflow
it. Each section still renders from its own area module (never
web.py); this module only joins them. Every Batch 20 section is
db-free, so no db_path threads through. Wired into the Status page by
status.page_html next to batch19_html.
"""
from __future__ import annotations

from . import contracts as contractsmod
from . import debugkata as debugkatamod
from . import diagrams as diagramsmod
from . import explcalib as explcalibmod
from . import forgetcurve as forgetcurvemod
from . import handout as handoutmod
from . import invariant as invariantmod
from . import katabank as katabankmod
from . import lessondiff as lessondiffmod
from . import lessonpin as lessonpinmod
from . import levelextremes as levelextremesmod
from . import peaktime as peaktimemod
from . import peerhelp as peerhelpmod
from . import readgroup as readgroupmod
from . import reteach as reteachmod
from . import tabmemory as tabmemorymod


def batch20_html() -> str:
    """Batch 20 home: one anchored subsection per shipped item.

    Improvements first, then the features — the same shape as
    batch19_html. Every section renders from its own area module
    (never web.py); all are db-free.
    """
    return "".join([
        "<h2 id='status-batch20'>Batch 20: deeper lessons, personal rhythm</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. The improvements diff lesson versions, "
        "pin lessons, print handouts, remember tabs, read calibration, "
        "stretch levels both ways, hint peer favorites, and gate visuals; "
        "the features add invariant and contract drills (types 89-90), "
        "kata libraries, reading groups, 30-day re-teaching, a personal "
        "forgetting curve, and peak-time suggestions.</p>",
        lessondiffmod.section_html(),
        lessonpinmod.section_html(),
        handoutmod.section_html(),
        tabmemorymod.section_html(),
        explcalibmod.section_html(),
        levelextremesmod.section_html(),
        peerhelpmod.section_html(),
        diagramsmod.section_html(),
        invariantmod.section_html(),
        contractsmod.section_html(),
        katabankmod.section_html(),
        debugkatamod.section_html(),
        readgroupmod.section_html(),
        reteachmod.section_html(),
        forgetcurvemod.section_html(),
        peaktimemod.section_html(),
    ])
