"""Batch 22 home: one anchored subsection per shipped item.

Improvements I-26, I-93, I-129, I-135, I-136, I-138–I-140 make time
honest and lessons calmer (timezone-explicit stamps, one <time>
element everywhere, real-file viewer, regen queue positions, A/B
phrasings kept by recall, read-aloud walkthroughs, dyslexia-friendly
type, instant reveals under reduced motion). Features F-102–F-105
and F-107–F-110 turn History into proof (owned headline, growth
rings, knowledge garden, time ledger, milestones, share-cards,
learning resume, delayed-test endorsements).

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): sixteen section imports plus the join would overflow
it. Each section still renders from its own area module (never
web.py); this module only joins them. The eight History sections
take the live db_path so the Status page demos real data; the eight
db-free improvement demos join without it. Wired into the Status
page by status.page_html next to batch21_html.
"""
from __future__ import annotations

from . import abphrase as abmod
from . import calmreplay as calmmod
from . import dyslexia as dysmod
from . import endorse as endorsemod
from . import growrings as growmod
from . import knowngarden as gardenmod
from . import learnresume as resumemod
from . import milestones as milesmod
from . import ownhead as ownmod
from . import readout as readmod
from . import realfile as realmod
from . import regenstat as regenmod
from . import sharecards as sharemod
from . import timeledger as ledgermod
from . import timetag as tagmod
from . import tztime as tzmod


def batch22_html(db_path: str = "") -> str:
    """Batch 22 home: one anchored subsection per shipped item.

    Improvements first, then the features — the same shape as
    batch21_html. History sections render live data off db_path;
    improvement demos are db-free.
    """
    return "".join([
        "<h2 id='status-batch22'>Batch 22: history of proof, calmer lessons</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. Time goes honest (explicit UTC stamps, "
        "one &lt;time&gt; element everywhere), lessons link to the real "
        "source line, flagged sections show their queue position, "
        "explainer order runs as a recall-scored experiment, "
        "walkthroughs speak and stay calm, and type turns readable on "
        "demand; History becomes proof — owned headline, growth rings, "
        "a blooming repo map, an honest time ledger, dated milestones, "
        "exportable share-cards, a verifiable resume, and endorsements "
        "from delayed tests only.</p>",
        tzmod.status_section_html(),
        tagmod.status_section_html(),
        realmod.status_section_html(),
        regenmod.status_section_html(),
        abmod.status_section_html(),
        readmod.status_section_html(),
        dysmod.status_section_html(),
        calmmod.status_section_html(),
        ownmod.section_html() if not db_path else
        f"<h3 id='{ownmod.STATUS_ANCHOR}'>Owned headline "
        "<small>(feature)</small></h3>" + ownmod.headline_html(db_path),
        growmod.section_html(db_path),
        gardenmod.section_html(db_path),
        ledgermod.section_html(db_path),
        milesmod.section_html(db_path),
        sharemod.section_html(db_path),
        resumemod.section_html(db_path),
        endorsemod.section_html(db_path),
    ])
