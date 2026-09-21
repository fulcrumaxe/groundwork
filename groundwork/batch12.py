"""Batch 12 home: one anchored subsection per shipped item (I-71..I-82, F-50..F-59).

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): sixteen section imports plus the join would overflow
it. Each section still renders from its own area module (never
web.py); this module only joins them. Every Batch 12 section is
db-free, so no db_path threads through. Wired into the Status page by
status.page_html next to batch11_html.
"""
from __future__ import annotations

from . import briefing as briefingmod
from . import coldattempt as coldattemptmod
from . import diffdial as diffdialmod
from . import elaboration as elaborationmod
from . import fading as fadingmod
from . import logbook as logbookmod
from . import optimistic as optimisticmod
from . import ownbanner as ownbannermod
from . import pressfx as pressfxmod
from . import quests as questsmod
from . import retest as retestmod
from . import selfexplain as selfexplainmod
from . import shelf as shelfmod
from . import skeletons as skeletonsmod
from . import typecontract as typecontractmod
from . import verdicts as verdictsmod


def batch12_html() -> str:
    """Batch 12 home: one anchored subsection per shipped item.

    Improvements first, then the eight learning-science features —
    the same shape as batch11_html. Every section renders from its
    own area module (never web.py); all are db-free.
    """
    return "".join([
        "<h2 id='status-batch12'>Batch 12: page themes and learning science</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. The themes restyle rendered pages "
        "through the head wire; the engines are db-free libraries.</p>",
        logbookmod.section_html(),
        shelfmod.section_html(),
        briefingmod.section_html(),
        verdictsmod.section_html(),
        ownbannermod.section_html(),
        pressfxmod.section_html(),
        skeletonsmod.section_html(),
        optimisticmod.section_html(),
        typecontractmod.section_html(),
        retestmod.section_html(),
        questsmod.section_html(),
        diffdialmod.section_html(),
        coldattemptmod.section_html(),
        fadingmod.section_html(),
        selfexplainmod.section_html(),
        elaborationmod.section_html(),
    ])
