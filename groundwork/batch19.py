"""Batch 19 home: one anchored subsection per shipped item.

Improvements I-104..I-109, I-112, I-115 make lessons link symbols,
replay traces, run own inputs, show before/after diffs, collapse long
source, explain why, prompt tries, and name their commit. Features
F-77..F-84 are eight new Due-queue exercise types (81-88).

Lives here instead of status.py because status.py sits exactly at
AREA_CAP (350): seventeen section imports plus the join would overflow
it. Each section still renders from its own area module (never
web.py); this module only joins them. Every Batch 19 section is
db-free, so no db_path threads through. Wired into the Status page by
status.page_html next to batch18_html.
"""
from __future__ import annotations

from . import analogy as analogymod
from . import apiguess as apiguessmod
from . import beforafter as beforaftermod
from . import boundary as boundarymod
from . import counterex as counterexmod
from . import feynman as feynmanmod
from . import lessonver as lessonvermod
from . import modelmap as modelmapmod
from . import protege as protegemod
from . import replay as replaymod
from . import rubberduck as rubberduckmod
from . import runinputs as runinputsmod
from . import srccollapse as srccollapsmod
from . import symlinks as symlinksmod
from . import tryprompts as trypromptsmod
from . import whyit as whyitmod


def batch19_html() -> str:
    """Batch 19 home: one anchored subsection per shipped item.

    Improvements first, then the eight study-drill features — the
    same shape as batch18_html. Every section renders from its own
    area module (never web.py); all are db-free.
    """
    return "".join([
        "<h2 id='status-batch19'>Batch 19: richer lessons, eight new drills</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. The improvements link symbols, replay "
        "traces, run own inputs, diff before/after, collapse source, "
        "explain why, prompt tries, and version lessons; the features "
        "are eight new Due-queue exercise types (81-88).</p>",
        symlinksmod.section_html(),
        replaymod.section_html(),
        runinputsmod.section_html(),
        beforaftermod.section_html(),
        srccollapsmod.section_html(),
        whyitmod.section_html(),
        trypromptsmod.section_html(),
        lessonvermod.section_html(),
        apiguessmod.section_html(),
        modelmapmod.section_html(),
        rubberduckmod.section_html(),
        protegemod.section_html(),
        feynmanmod.section_html(),
        analogymod.section_html(),
        counterexmod.section_html(),
        boundarymod.section_html(),
    ])
