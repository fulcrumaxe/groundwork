"""Batch 13 home: one anchored subsection per shipped item (I-83..I-90, F-60..F-67).

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): sixteen section imports plus the join would overflow
it. Each section still renders from its own area module (never
web.py); this module only joins them. Every Batch 13 section is
db-free, so no db_path threads through. Wired into the Status page by
status.page_html next to batch12_html.
"""
from __future__ import annotations

from . import calibdrill as calibdrillmod
from . import confweight as confweightmod
from . import density as densitymod
from . import dualcode as dualcodemod
from . import errpage as errpagemod
from . import formerr as formerrmod
from . import interleave as interleavemod
from . import ogtags as ogtagsmod
from . import overconf as overconfmod
from . import pageicon as pageiconmod
from . import predict as predictmod
from . import responsive as responsivemod
from . import retrieval as retrievalmod
from . import scrollbar as scrollbarmod
from . import selection as selectionmod
from . import spacingopt as spacingoptmod


def batch13_html() -> str:
    """Batch 13 home: one anchored subsection per shipped item.

    Improvements first, then the eight learning-science features —
    the same shape as batch12_html. Every section renders from its
    own area module (never web.py); all are db-free.
    """
    return "".join([
        "<h2 id='status-batch13'>Batch 13: chrome robustness and study science</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. The chrome items restyle the head "
        "wire or harden error paths; the engines are db-free libraries.</p>",
        errpagemod.section_html(),
        formerrmod.section_html(),
        selectionmod.section_html(),
        scrollbarmod.section_html(),
        pageiconmod.section_html(),
        ogtagsmod.section_html(),
        densitymod.section_html(),
        responsivemod.section_html(),
        dualcodemod.section_html(),
        interleavemod.section_html(),
        spacingoptmod.section_html(),
        retrievalmod.section_html(),
        predictmod.section_html(),
        confweightmod.section_html(),
        calibdrillmod.section_html(),
        overconfmod.section_html(),
    ])
