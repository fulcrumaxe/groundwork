"""Batch 28 home: one anchored subsection per shipped item.

Improvements I-186–I-188/I-190–I-192 make hints, review flow, and
practice variants honest (scratch runs unlock hint tiers without
grading, stuck time unlocks tiers, free nudge reveals, post-answer
next lists, practice-similar siblings, bonus attempts that skip
stats). I-189 needs per-card hint-usage records no table stores
(schema frozen), so it stays uncrossed; I-193/I-194 verified
pre-shipped (disputes + maintainer queue wired since Batch 3).
Features F-166/F-170/F-174/F-175/F-178/F-180/F-181 stay solo-honest
(owned-proofs gradebook CSV, guardian aggregate view, curriculum
matrix, syllabus gates, office-hours bring-list, verifiable
certificates, open badges); F-184 verified pre-shipped
(blindspots). The classroom/team items in between
(F-167–F-169/F-171–F-173/F-176/F-177/F-179/F-183/F-187/F-188) need
multi-user identity this single-user app has no honest source for,
so they stay uncrossed.

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): thirteen section imports plus the join would
overflow it. Each section still renders from its own area module
(never web.py); this module only joins them. Wired into the Status
page by status.page_html next to batch27_html.
"""
from __future__ import annotations

from . import asknudge as asknudgemod
from . import bonus as bonusmod
from . import certhash as certhashmod
from . import curricmap as curricmapmod
from . import gradebook as gradebookmod
from . import guardian as guardianmod
from . import nextup as nextupmod
from . import officehours as officehoursmod
from . import openbadge as openbadgemod
from . import scratchhint as scratchhintmod
from . import similar as similarmod
from . import stuckhint as stuckhintmod
from . import syllabus as syllabusmod


def batch28_html(db_path: str = "") -> str:
    """Batch 28 home: one anchored subsection per shipped item.

    Improvements first, then the features -- the same shape as
    batch27_html. Sections render from their own area modules;
    gradebook takes the live db_path, the rest are static.
    """
    return "".join([
        "<h2 id='status-batch28'>Batch 28: hints earn their keep, proofs travel</h2>"
        "<p>Six improvements plus seven features, each a focused "
        "module under 350 lines. Hints get honest -- scratch runs "
        "unlock tiers, stuck time unlocks tiers, free nudges, "
        "what-next lists, practice-similar siblings, bonus attempts "
        "that skip stats; proofs travel -- gradebook CSV, guardian "
        "view, curriculum matrix, syllabus gates, office-hours "
        "bring-list, verifiable certificates, open badges.</p>",
        scratchhintmod.section_html(),
        stuckhintmod.section_html(),
        asknudgemod.section_html(),
        nextupmod.section_html(),
        similarmod.section_html(),
        bonusmod.section_html(),
        gradebookmod.status_html(db_path),
        guardianmod.section_html(),
        curricmapmod.section_html(),
        syllabusmod.section_html(),
        officehoursmod.section_html(),
        certhashmod.status_section_html(),
        openbadgemod.status_section_html(),
    ])
