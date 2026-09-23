"""Batch 21 home: one anchored subsection per shipped item.

Improvements I-92, I-126, I-127, I-130–I-132, I-134 make lessons
readable and navigable (scrollable tables, call graphs, sequence
diagrams, attached images, dependency jump links, deterministic
cycle-breaking, confusing-section flags). Features F-93–F-100 make
the Due queue adaptive (sleep-aware dues, cognitive-load guard, flow
detection, frustration relief, boredom rung-ups, style tuning, skill
atoms, remediation paths). I-129 (real-file viewer) was cut: no
/files route exists, so it stays unshipped.

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): fifteen section imports plus the join would overflow
it. Each section still renders from its own area module (never
web.py); this module only joins them. Every Batch 21 section is
db-free, so no db_path threads through. Wired into the Status page by
status.page_html next to batch20_html.
"""
from __future__ import annotations

from . import boredom as boredommod
from . import callgraph as callgraphmod
from . import cogniload as cogniloadmod
from . import confusing as confusingmod
from . import depcycle as depcyclemod
from . import flowdetect as flowdetectmod
from . import frustcatch as frustcatchmod
from . import imgattach as imgattachmod
from . import lessondeps as lessondepsmod
from . import remedpath as remedpathmod
from . import seqdiag as seqdiagmod
from . import skillatoms as skillatomsmod
from . import sleepsched as sleepschedmod
from . import stylemix as stylemixmod
from . import tablescroll as tablescrollmod


def batch21_html() -> str:
    """Batch 21 home: one anchored subsection per shipped item.

    Improvements first, then the features — the same shape as
    batch20_html. Every section renders from its own area module
    (never web.py); all are db-free. skillatoms and remedpath join
    via status_section because their section_html renders page
    content (atoms list / remediation note), not a status block.
    """
    return "".join([
        "<h2 id='status-batch21'>Batch 21: readable lessons, adaptive queue</h2>"
        "<p>Seven improvements plus eight features, each a focused "
        "module under 350 lines. The improvements keep wide tables "
        "readable, draw call graphs and sequence diagrams, attach "
        "images, link lesson dependencies, break dependency cycles "
        "deterministically, and flag confusing sections; the features "
        "schedule around sleep, guard cognitive load, detect flow, "
        "relieve frustration, cure boredom one Bloom rung up, tune to "
        "learning style, split misses into skill atoms, and queue "
        "prerequisites ahead of retries.</p>",
        tablescrollmod.section_html(),
        callgraphmod.section_html(),
        seqdiagmod.section_html(),
        imgattachmod.section_html(),
        lessondepsmod.section_html(),
        depcyclemod.section_html(),
        confusingmod.section_html(),
        sleepschedmod.section_html(),
        cogniloadmod.section_html(),
        flowdetectmod.section_html(),
        frustcatchmod.section_html(),
        boredommod.section_html(),
        stylemixmod.section_html(),
        skillatomsmod.status_section(),
        remedpathmod.status_section(),
    ])
