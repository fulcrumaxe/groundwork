"""Batch 27 home: one anchored subsection per shipped item.

Improvements I-178–I-185 sharpen code cards where learners meet
them (inline cloze blanks, signature skeletons with per-param ticks,
where-live tree pickers, measured reference runtimes, tailored
timeout feedback, plain-language sandbox errors, run-without-
submitting scratch runs). I-181 was already shipped as grading.py
disclosures, so it joins as a cross-off, not a new section.
Features F-149/F-154/F-160–F-162/F-164 stay useful and honest (the
carbon note, layered onboarding paths, handoff packs, interview
loops, contractor ramp packs, self-assigned study plans); F-150 and
F-155 were already shipped as anniversary recaps and the onboard
checklist, and F-151–F-153/F-156–F-159/F-163 need multi-user data
this single-user app has no honest source for, so they stay
uncrossed. F-165 was verified pre-shipped during backfill.

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): thirteen section imports plus the join would
overflow it. Each section still renders from its own area module
(never web.py); this module only joins them. Wired into the Status
page by status.page_html next to batch26_html.
"""
from __future__ import annotations

from . import carbon as carbonmod
from . import clozein as clozeinmod
from . import errplain as errplainmod
from . import handoff as handoffmod
from . import interviewloop as interviewloopmod
from . import layerpath as layerpathmod
from . import ramppack as ramppackmod
from . import refms as refmsmod
from . import scratchrun as scratchrunmod
from . import selfassign as selfassignmod
from . import sigslots as sigslotsmod
from . import timefb as timefbmod
from . import treepick as treepickmod


def batch27_html(db_path: str = "") -> str:
    """Batch 27 home: one anchored subsection per shipped item.

    Improvements first, then the features -- the same shape as
    batch26_html. Sections render from their own area modules;
    carbon/handoff take the live db_path, the rest are static.
    """
    return "".join([
        "<h2 id='status-batch27'>Batch 27: sharper code cards, honest planning</h2>"
        "<p>Seven improvements plus six features, each a focused "
        "module under 350 lines. Code cards get sharper -- inline "
        "cloze blanks, signature skeletons, tree pickers, measured "
        "reference runtimes, tailored timeouts, plain-language "
        "errors, scratch runs; planning stays honest -- the carbon "
        "note, layered onboarding paths, handoff packs, interview "
        "loops, ramp packs, self-assigned plans.</p>",
        clozeinmod.section_html(),
        sigslotsmod.section_html(),
        treepickmod.section_html(),
        refmsmod.section_html(),
        timefbmod.section_html(),
        errplainmod.section_html(),
        scratchrunmod.section_html(),
        carbonmod.status_html(db_path),
        layerpathmod.section_html(),
        handoffmod.status_html(db_path),
        interviewloopmod.section_html(),
        ramppackmod.section_html(db_path),
        selfassignmod.section_html(),
    ])
