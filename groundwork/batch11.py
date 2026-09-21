"""Batch 11 home: one anchored subsection per shipped item (I-63..I-70, F-42..F-49).

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): sixteen section imports plus the join would overflow
it. Each section still renders from its own area module (never
web.py); this module only joins them. Every Batch 11 section is
db-free, so no db_path threads through. Wired into the Status page by
status.page_html next to batch10_html.
"""
from __future__ import annotations

from . import backfill as backfillmod
from . import cacheinv as cacheinvmod
from . import cipipe as cipipemod
from . import confslider as confslidermod
from . import donehero as doneheromod
from . import emptyart as emptyartmod
from . import flagcut as flagcutmod
from . import focusrings as focusringsmod
from . import hinttiers as hinttiersmod
from . import idempot as idempotmod
from . import pageapi as pageapimod
from . import radius as radiusmod
from . import ratelimit as ratelimitmod
from . import spacing as spacingmod
from . import taptargets as taptargetsmod
from . import webhook as webhookmod


def batch11_html() -> str:
    """Batch 11 home: one anchored subsection per shipped item.

    Improvements first, then the eight new exercise types — the same
    shape as batch10_html. Every section renders from its own area
    module (never web.py); all are db-free.
    """
    return "".join([
        "<h2 id='status-batch11'>Batch 11: reading polish and backend exercises</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. The eight exercise types also emit "
        "into lesson modules via the pipeline.</p>",
        hinttiersmod.section_html(),
        confslidermod.section_html(),
        focusringsmod.section_html(),
        taptargetsmod.section_html(),
        radiusmod.section_html(),
        spacingmod.section_html(),
        emptyartmod.section_html(),
        doneheromod.section_html(),
        cipipemod.section_html(),
        flagcutmod.section_html(),
        backfillmod.section_html(),
        pageapimod.section_html(),
        cacheinvmod.section_html(),
        idempotmod.section_html(),
        ratelimitmod.section_html(),
        webhookmod.section_html(),
    ])
