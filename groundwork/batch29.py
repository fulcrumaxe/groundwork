"""Batch 29 home: one anchored subsection per shipped item.

Improvements I-195/I-197/I-199–I-202/I-205/I-206 make the queue
respect the learner's day (accepted disputes quarantine the card and
mint a retry, changed repeats show the prior answer, one submit per
card per 5s, full keyboard answer-rate-advance, fuller FSRS updates
fit to personal recall history, desired-retention workload preview,
daily cap with load-balanced overflow, weekend light mode). I-196
needs card-authorship records no table stores (schema frozen), so it
stays uncrossed; I-198 verified pre-shipped (personal bests since
Batch 4). Features F-182/F-185/F-186/F-189–F-192/F-195 stay
solo-honest (knowledge half-life, on-call prep packs, commander
certification track, compliance verification, security and
accessibility champion tracks, contributor ladder, workshop sprints);
F-193 needs a user directory plus availability signals this
single-user app has no honest source for, so it stays uncrossed
(F-194 needs money rails; F-195 backfilled in backlog order).

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): sixteen section imports plus the join would
overflow it. Each section still renders from its own area module
(never web.py); this module only joins them. Wired into the Status
page by status.page_html next to batch28_html.
"""
from __future__ import annotations

from . import a11ychamp as a11ychampmod
from . import answerhist as answerhistmod
from . import cmdtrack as cmdtrackmod
from . import comptrack as comptrackmod
from . import dailycap as dailycapmod
from . import fsrs45 as fsrs45mod
from . import halflife as halflifemod
from . import keyflow as keyflowmod
from . import lightdays as lightdaysmod
from . import osslader as ossladermod
from . import oncallpack as oncallpackmod
from . import quarantine as quarantinemod
from . import retention as retentionmod
from . import secchamp as secchampmod
from . import spamguard as spamguardmod
from . import workshop as workshopmod


def batch29_html(db_path: str = "") -> str:
    """Batch 29 home: one anchored subsection per shipped item.

    Improvements first, then the features -- the same shape as
    batch28_html. Sections render from their own area modules;
    halflife/secchamp/a11ychamp take the live db_path, the rest
    are static.
    """
    return "".join([
        "<h2 id='status-batch29'>Batch 29: the queue respects the day, tracks prove the craft</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. The queue respects the day -- dispute "
        "quarantine, answer history, double-submit guard, full keyboard "
        "flow, personal FSRS fit, retention preview, daily cap, light "
        "days; tracks prove the craft -- half-life report, on-call "
        "packs, commander track, compliance verification, security and "
        "accessibility champions, contributor ladder, workshop sprints.</p>",
        quarantinemod.section_html(),
        answerhistmod.section_html(),
        spamguardmod.section_html(),
        keyflowmod.section_html(),
        fsrs45mod.section_html(),
        retentionmod.section_html(),
        dailycapmod.section_html(),
        lightdaysmod.section_html(),
        halflifemod.status_html(db_path),
        oncallpackmod.section_html(),
        cmdtrackmod.section_html(),
        comptrackmod.section_html(),
        secchampmod.section_html(db_path),
        a11ychampmod.section_html(db_path),
        ossladermod.section_html(),
        workshopmod.section_html(),
    ])
