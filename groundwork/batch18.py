"""Batch 18 home: one anchored subsection per shipped item (I-91..I-103, F-69..F-76).

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): sixteen section imports plus the join would overflow
it. Each section still renders from its own area module (never
web.py); this module only joins them. Every Batch 18 section is
db-free, so no db_path threads through. Wired into the Status page by
status.page_html next to batch13_html.
"""
from __future__ import annotations

from . import contrast as contrastmod
from . import emoji as emojimod
from . import explainflip as explainflipmod
from . import fartransfer as fartransfermod
from . import fluency as fluencymod
from . import glossary as glossmod
from . import incident as incidentmod
from . import interview as interviewmod
from . import motion as motionmod
from . import nameguess as nameguessmod
from . import pagesnap as pagesnapmod
from . import parsons as parsonsmod
from . import premortem as premortemmod
from . import pressure as pressuremod
from . import tokens as tokensmod
from . import transfer as transfermod


def batch18_html() -> str:
    """Batch 18 home: one anchored subsection per shipped item.

    Improvements first, then the eight fluency/transfer features —
    the same shape as batch13_html. Every section renders from its
    own area module (never web.py); all are db-free.
    """
    return "".join([
        "<h2 id='status-batch18'>Batch 18: stable rendering and fluency drills</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. The improvements steady Parsons lists, "
        "icons, motion, contrast, explainer order, and jargon; the "
        "features are eight new Due-queue exercise types (73-80) plus "
        "the understand bloom tier.</p>",
        parsonsmod.section_html(),
        tokensmod.section_html(),
        pagesnapmod.section_html(),
        emojimod.section_html(),
        motionmod.section_html(),
        contrastmod.section_html(),
        explainflipmod.section_html(),
        glossmod.section_html(),
        interviewmod.section_html(),
        transfermod.section_html(),
        fartransfermod.section_html(),
        pressuremod.section_html(),
        incidentmod.section_html(),
        premortemmod.section_html(),
        fluencymod.section_html(),
        nameguessmod.section_html(),
    ])
