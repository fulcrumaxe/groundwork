"""Batch 24 home: one anchored subsection per shipped item.

Improvements I-154–I-161 make practice honest and tactile (a real
code editor with Tab indent, a visible Run button with its shortcut,
inline sandbox output, yours-vs-expected diffs, grade-0 give-up
reveals, lapse-counted honest give-ups, per-blank partial credit,
retry-wrong-blanks-only). Features F-120 and F-122–F-128 shape the
session rhythm and company (5/10/20-minute playlists, rest-day
affirmations, 30-day comeback recaps, the anti-streak pledge, buddy
pings, repo-overlap matching, co-op splits, coffee wagers on delayed
recalls). I-152 stays unshipped: draft preservation already lives in
web.py GLOBAL_JS. I-142 and F-118 stay unshipped from Batch 23: no
audio assets exist anywhere, so transcripts and ambient files have no
data source.

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): sixteen section imports plus the join would
overflow it. Each section still renders from its own area module
(never web.py); this module only joins them. Wired into the Status
page by status.page_html next to batch23_html.
"""
from __future__ import annotations

from . import antistreak as antistreakmod
from . import buddymatch as buddymatchmod
from . import buddyping as buddypingmod
from . import codeedit as codeeditmod
from . import comeback as comebackmod
from . import coop as coopmod
from . import giveup as giveupmod
from . import outdiff as outdiffmod
from . import partial as partialmod
from . import playlists as playlistsmod
from . import restday as restdaymod
from . import retryblanks as retryblanksmod
from . import reveal as revealmod
from . import runkey as runkeymod
from . import sandout as sandoutmod
from . import wagers as wagersmod


def batch24_html(db_path: str = "") -> str:
    """Batch 24 home: one anchored subsection per shipped item.

    Improvements first, then the features — the same shape as
    batch23_html. Sections render from their own area modules;
    db_path is accepted for call-site shape and ignored.
    """
    _ = db_path
    return "".join([
        "<h2 id='status-batch24'>Batch 24: honest practice, gentle rhythm</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. Practice turns honest and tactile — "
        "a real editor, a visible Run button, inline sandbox output, "
        "side-by-side diffs, grade-0 reveals, lapse-counted give-ups, "
        "per-blank credit, wrong-blanks-only retries; the rhythm turns "
        "gentle — minute-sized playlists, rest-day affirmations, "
        "comeback recaps, an anti-streak pledge, buddy pings and "
        "matching, co-op splits, and coffee wagers on delayed "
        "recalls.</p>",
        codeeditmod.section_html(),
        runkeymod.section_html(),
        sandoutmod.section_html(),
        outdiffmod.section_html(),
        revealmod.section_html(),
        giveupmod.section_html(),
        partialmod.section_html(),
        retryblanksmod.section_html(),
        playlistsmod.section_html(),
        restdaymod.section_html(),
        comebackmod.section_html(),
        antistreakmod.section_html(),
        buddypingmod.section_html(),
        buddymatchmod.section_html(),
        coopmod.section_html(),
        wagersmod.status_section_html(),
    ])
