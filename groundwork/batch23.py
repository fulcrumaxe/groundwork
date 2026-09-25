"""Batch 23 home: one anchored subsection per shipped item.

Improvements I-141, I-143–I-146, I-148–I-150 make lessons
listenable, social, gentle, votable, weighted, celebratory,
digestible, and honest about retirements (audio summaries,
twin-pane buddy view, still-with-us nudge, difficulty votes and
their queue weights, unlock badges, weekly digest, retired-lesson
archive). Features F-111–F-117 and F-119 turn proof into play
(party trick, teaching certificates, concept badges, private
showcase, theme unlocks, library identity, effort mascot, focus
timer). I-142 and F-118 stay unshipped: no audio assets exist
anywhere, so transcripts and ambient files have no data source.

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): sixteen section imports plus the join would
overflow it. Each section still renders from its own area module
(never web.py); this module only joins them. Live-data sections
take db_path so the Status page demos real data; db-free demos
join without it. Wired into the Status page by status.page_html
next to batch22_html.
"""
from __future__ import annotations

from . import archiveless as archivemod
from . import audiosum as audiomod
from . import avatar as avatarmod
from . import buddyview as buddymod
from . import conceptbadges as badgemod
from . import diffvote as votemod
from . import diffweights as weightsmod
from . import focustimer as focusmod
from . import mascot as mascotmod
from . import partytrick as partymod
from . import readnudge as nudgemod
from . import showcase as showmod
from . import teachcert as certmod
from . import themeunlock as thememod
from . import unlockfx as unlockmod
from . import weekdigest as digestmod


def batch23_html(db_path: str = "") -> str:
    """Batch 23 home: one anchored subsection per shipped item.

    Improvements first, then the features — the same shape as
    batch22_html. Live sections render off db_path; db-free demos
    join without it.
    """
    return "".join([
        "<h2 id='status-batch23'>Batch 23: listenable lessons, playful proof</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. Lessons speak their summaries, host "
        "a friend side by side, nudge gently after ten idle minutes, "
        "take difficulty votes that reshape the queue, pop when newly "
        "unlocked, digest the week's code changes, and archive "
        "retirements with reasons; proof turns playful — party tricks "
        "from the owned list, certificates per pack, collectible "
        "badges in a private showcase, milestone palettes, a library "
        "mark, an effort-only mascot, and focus blocks auto-filled "
        "from the queue.</p>",
        audiomod.status_section_html(),
        buddymod.section_html(),
        nudgemod.section_html(),
        votemod.status_section_html(),
        weightsmod.status_section_html(),
        unlockmod.section_html(),
        digestmod.section_html(),
        archivemod.section_html(),
        (partymod.section_html(db_path) + partymod.status_section_html()),
        (certmod.section_html(db_path) + certmod.status_section_html()),
        badgemod.section_html(),
        (showmod.gallery_html(db_path) + showmod.status_section_html()),
        (thememod.gallery_html(db_path) + thememod.status_section_html()),
        (avatarmod.box_html(db_path) + avatarmod.status_section_html()),
        (mascotmod.line_html(db_path) + mascotmod.status_section_html()),
        focusmod.status_section_html(),
    ])
