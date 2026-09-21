"""Batch 10 home: one anchored subsection per shipped item (I-55..I-62, F-34..F-41).

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): sixteen section imports plus the join would overflow
it. Each section still renders from its own area module (never
web.py); this module only joins them. Every Batch 10 section is
db-free, so no db_path threads through. Wired into the Status page by
status.page_html next to batch9_html.
"""
from __future__ import annotations

from . import bloomchips as bloomchipsmod
from . import carets as caretsmod
from . import cliux as cliuxmod
from . import codelines as codelinesmod
from . import containerize as containerizemod
from . import crashdump as crashdumpmod
from . import depupgrade as depupgrademod
from . import flame as flamemod
from . import highlight as highlightmod
from . import licensecheck as licensecheckmod
from . import logread as logreadmod
from . import metrics as metricsmod
from . import ownedbadge as ownedbadgemod
from . import progbar as progbarmod
from . import stagger as staggermod
from . import wordmark as wordmarkmod


def batch10_html() -> str:
    """Batch 10 home: one anchored subsection per shipped item.

    Improvements first, then the eight new exercise types — the same
    shape as batch9_html. Every section renders from its own area
    module (never web.py); all are db-free.
    """
    return "".join([
        "<h2 id='status-batch10'>Batch 10: header polish and ops exercises</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. The eight exercise types also emit "
        "into lesson modules via the pipeline.</p>",
        wordmarkmod.section_html(),
        bloomchipsmod.section_html(),
        progbarmod.section_html(),
        ownedbadgemod.section_html(),
        staggermod.section_html(),
        caretsmod.section_html(),
        codelinesmod.section_html(),
        highlightmod.section_html(),
        cliuxmod.section_html(),
        logreadmod.section_html(),
        metricsmod.section_html(),
        flamemod.section_html(),
        crashdumpmod.section_html(),
        depupgrademod.section_html(),
        licensecheckmod.section_html(),
        containerizemod.section_html(),
    ])
