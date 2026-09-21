"""Status page: the machine room with a home for every section.

All Status sections assemble here — CI, hooks, CLI, MCP, exports,
sharing, module health, disputes, API, sitemap, seed, storage. The web
Handler keeps one delegation line; new sections land in this file or in
their own area module's section_html, never in web.py.
"""
from __future__ import annotations

from pathlib import Path

from . import db as dbmod
from . import a11yaudit as a11yauditmod
from . import apidesign as apidesignmod
from . import archived as archivedmod
from . import autofocus as autofocusmod
from . import batch10 as batch10mod, batch11 as batch11mod, batch12 as batch12mod
from . import autoscroll as autoscrollmod
from . import bisect as bisectmod
from . import blindspots as blindmod
from . import buttons as buttonsmod
from . import canonurl as canonurlmod
from . import cardlinks as cardlinksmod
from . import changelog as changelogmod
from . import chiplinks as chiplinksmod
from . import clickcards as clickcardsmod
from . import collapse as collapsemod
from . import commitmsg as commitmsgmod
from . import configex as configexmod
from . import crumbs as crumbsmod
from . import cssfix as cssfixmod
from . import darkmode as darkmodemod
from . import deadcode as deadcodemod
from . import diretro as diretromod
from . import disputes as dismod
from . import docdoctest as docdoctestmod
from . import errbranch as errbranchmod
from . import extlinks as extlinksmod
from . import fontstack as fontstackmod
from . import footnav as footnavmod
from . import fuzztriage as fuzztriagemod
from . import golf as golfmod
from . import i18n as i18nmod
from . import inputaudit as inputauditmod
from . import levelcarry as levelcarrymod
from . import letter as lettermod
from . import linkcheck as linkcheckmod
from . import logretro as logretromod
from . import mcp as mcplib
from . import memprofile as memprofilemod
from . import migration as migrationmod
from . import minisession as minisessionmod
from . import modfilter as modfiltermod
from . import modpages as modpagesmod
from . import modularity as modularitymod
from . import northstar as northstarmod
from . import originguard as originguardmod
from . import pageids as pageidsmod
from . import pager as pagermod
from . import perffix as perffixmod
from . import proptest as proptestmod
from . import racehunt as racehuntmod
from . import rebase as rebasemod
from . import recent as recentmod
from . import regexex as regexexmod
from . import renameex as renameexmod
from . import repro as repromod
from . import resume as resumemod
from . import reviewed as reviewedmod
from . import rollback as rollbackmod
from . import scrollpos as scrollposmod
from . import search as searchmod
from . import secretscan as secretscanmod
from . import sitenav as sitenavmod
from . import smell as smellmod
from . import snapshot as snapshotmod
from . import specwrite as specwritemod
from . import sqlex as sqlexmod
from . import threatmodel as threatmodelmod
from . import tools as toolsmod
from . import unsaved as unsavedmod
from . import tochighlight as tochighlightmod
from . import sched as schedmod
from . import storage as storagemod
from . import typeanno as typeannomod
from . import typescale as typescalemod


BATCH5 = [
    ("titles", "improvement", "Unique page titles",
     "Every page names its context; browser tabs stay distinct.",
     "groundwork/titles.py"),
    ("empty", "improvement", "Empty states with next action",
     "No dead ends: every dry page offers a next step.",
     "groundwork/empty.py"),
    ("palette", "improvement", "Palette CSS variables",
     "One :root token source for ink, paper, accents, pass/fail/stale.",
     "groundwork/palette.py"),
    ("copylink", "improvement", "Copy-link anchors",
     "Every lesson section carries its own deep link.",
     "groundwork/copylink.py"),
    ("readprogress", "improvement", "Reading-progress bar",
     "A slim bar shows how far through a module page you are.",
     "groundwork/readprogress.py"),
    ("charcount", "improvement", "Char/line counts",
     "Code textareas report chars, lines and words as you type.",
     "groundwork/charcount.py"),
    ("printcss", "improvement", "Print stylesheet",
     "Lessons print cleanly as serif study sheets.",
     "groundwork/printcss.py"),
    ("answerguard", "improvement", "Empty-answer guard",
     "Blank submits get an inline warning instead of silence.",
     "groundwork/answerguard.py"),
    ("session", "feature", "Session-end summary",
     "Answered, accuracy and what returns when — the 5-minute debrief.",
     "groundwork/session.py"),
    ("garden", "feature", "Gardener stages",
     "Concepts grow seed to sprout to tree; no streaks.",
     "groundwork/garden.py"),
    ("cover", "feature", "Cover colors",
     "Each module gets a stable cover hue from its repo hash.",
     "groundwork/cover.py"),
    ("filemap", "feature", "File-map mini-view",
     "Breadcrumbs show where a concept sits in the repo tree.",
     "groundwork/filemap.py"),
    ("prereq", "feature", "Prerequisite chain",
     "Understand-X-first path with jump links atop each module.",
     "groundwork/prereq.py"),
    ("exitticket", "feature", "Exit tickets",
     "Each lesson ends with one ungraded retrieval question.",
     "groundwork/exitticket.py"),
    ("misconceptions", "feature", "Misconception callouts",
     "Lessons flag the wrong idea learners most often hold.",
     "groundwork/misconceptions.py"),
    ("lessonnotes", "feature", "Private lesson notes",
     "A per-lesson scratchpad kept in your browser only.",
     "groundwork/lessonnotes.py"),
]


def batch5_html() -> str:
    """Batch 5 home: one anchored subsection per shipped item."""
    parts = ["<h2 id='status-batch5'>Batch 5: eight and eight</h2>"
             "<p>Eight improvements plus eight features, each a focused "
             "module under 350 lines. Page wiring lands next; every item "
             "is inspectable here meanwhile.</p>"]
    for slug, kind, title, blurb, mod in BATCH5:
        parts.append(
            f"<h3 id='status-b5-{slug}'>{title} <small>({kind})</small></h3>"
            f"<p>{blurb} <code>{mod}</code>.</p>")
    return "".join(parts)


def batch6_html(db_path: str) -> str:
    """Batch 6 home: one anchored subsection per shipped item.

    Each section renders from its own area module (never web.py);
    db_path threads through to the modules that accept it.
    """
    return "".join([
        "<h2 id='status-batch6'>Batch 6: search, trails, and new exercises</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. The eight exercise types also emit "
        "into lesson modules via the pipeline.</p>",
        searchmod.section_html(),
        crumbsmod.section_html(),
        levelcarrymod.section_html(),
        tochighlightmod.status_html(),
        cardlinksmod.section_html(db_path),
        pagermod.section_html(db_path),
        footnavmod.section_html_status(),
        scrollposmod.section_html(),
        smellmod.section_html(db_path),
        renameexmod.section_html(db_path),
        golfmod.section_html(),
        diretromod.section_html(db_path),
        errbranchmod.section_html(db_path),
        logretromod.section_html(db_path),
        typeannomod.section_html(db_path),
        docdoctestmod.section_html(),
    ])


def batch7_html(db_path: str) -> str:
    """Batch 7 home: one anchored subsection per shipped item.

    Each section renders from its own area module (never web.py);
    db_path threads through to the modules that accept it.
    """
    return "".join([
        "<h2 id='status-batch7'>Batch 7: library scale and new exercises</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. The eight exercise types also emit "
        "into lesson modules via the pipeline.</p>",
        clickcardsmod.section_html(),
        reviewedmod.section_html(),
        modfiltermod.section_html(),
        modpagesmod.section_html(db_path),
        chiplinksmod.section_html(db_path),
        recentmod.section_html(),
        unsavedmod.section_html(),
        autoscrollmod.section_html(),
        proptestmod.section_html(),
        fuzztriagemod.section_html(),
        perffixmod.section_html(),
        memprofilemod.section_html(),
        racehuntmod.section_html(db_path),
        deadcodemod.section_html(),
        configexmod.section_html(db_path),
        apidesignmod.section_html(),
    ])


def batch8_html() -> str:
    """Batch 8 home: one anchored subsection per shipped item.

    Each section renders from its own area module (never web.py);
    every Batch 8 section is db-free, so no db_path threads through.
    """
    return "".join([
        "<h2 id='status-batch8'>Batch 8: nav, guards, and new exercises</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. The eight exercise types also emit "
        "into lesson modules via the pipeline.</p>",
        extlinksmod.section_html(),
        canonurlmod.section_html(),
        originguardmod.section_html(),
        buttonsmod.section_html(),
        pageidsmod.section_html(),
        archivedmod.section_html(),
        sitenavmod.section_html(),
        autofocusmod.section_html(),
        specwritemod.section_html(),
        commitmsgmod.section_html(),
        changelogmod.section_html(),
        repromod.section_html(),
        bisectmod.section_html(),
        rebasemod.section_html(),
        migrationmod.section_html(),
        rollbackmod.section_html(),
    ])


def batch9_html() -> str:
    """Batch 9 home: one anchored subsection per shipped item.

    Each section renders from its own area module (never web.py).
    Improvements first, then the eight new exercise types.
    """
    return "".join([
        "<h2 id='status-batch9'>Batch 9: queue flow and new exercises</h2>"
        "<p>Eight improvements plus eight features, each a focused "
        "module under 350 lines. The eight exercise types also emit "
        "into lesson modules via the pipeline.</p>",
        collapsemod.section_html(),
        minisessionmod.section_html(),
        resumemod.section_html(),
        snapshotmod.section_html(),
        linkcheckmod.section_html(),
        darkmodemod.section_html(),
        typescalemod.section_html(),
        fontstackmod.section_html(),
        threatmodelmod.section_html(),
        secretscanmod.section_html(),
        inputauditmod.section_html(),
        a11yauditmod.section_html(),
        i18nmod.section_html(),
        regexexmod.section_html(),
        sqlexmod.section_html(),
        cssfixmod.section_html(),
    ])


def page_html(db_path: str) -> str:
    """Visible home for the non-page items, plus the area sections."""
    root = Path(__file__).resolve().parent.parent
    ci = root / ".github" / "workflows" / "groundwork.yml"
    hook = root / "hooks" / "pre-commit"
    now = schedmod.iso(schedmod.utcnow())
    con = dbmod.connect(db_path)
    try:
        due = con.execute(
            "SELECT COUNT(*) FROM cards WHERE due <= ? AND stale = 0",
            (now,)).fetchone()[0]
        cards = con.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        mods = con.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
    finally:
        con.close()
    tools = sorted(m[5:] for m in dir(mcplib.MCPServer)
                   if m.startswith("tool_"))
    ci_mark = ("<span class='status-ok'>present</span>"
               if ci.exists() else "<span class='status-missing'>missing</span>")
    hook_ok = hook.exists() and bool(hook.stat().st_mode & 0o111)
    hook_mark = ("<span class='status-ok'>present, executable</span>"
                 if hook_ok
                 else "<span class='status-missing'>missing or not executable</span>")
    return "".join([
        "<p>Machine-room items that have no page of their own live here, "
        "so the tour can point at them.</p>",
        f"<h2 id='status-ci'>CI workflow</h2><p>{ci_mark} — "
        "<code>.github/workflows/groundwork.yml</code>, runs the test suite on push.</p>",
        f"<h2 id='status-hooks'>Pre-commit hook</h2><p>{hook_mark} — "
        "<code>hooks/pre-commit</code>.</p>",
        f"<h2 id='status-cli'>CLI review</h2><p><code>python3 -m groundwork "
        f"review --limit 20</code> — {due} cards due right now.</p>",
        f"<h2 id='status-mcp'>MCP endpoint</h2><p><code>python3 -m groundwork mcp</code> "
        f"and <code>POST /mcp</code> — tools: {', '.join(tools)}.</p>",
        f"<h2 id='status-exports'>Exports</h2><p>{cards} cards in {mods} modules — "
        "<a href='/export/anki.tsv'>Anki TSV</a> · "
        "<a href='/feed.xml'>RSS feed</a> · "
        "<span id='status-csv'><a href='/export/reviews.csv'>"
        "Review log CSV</a></span>.</p>",
        "<h2 id='status-share'>Module sharing</h2>"
        "<p><code>python3 -m groundwork export-module --module ID --out share.json</code> "
        "downloads a module; <code>python3 -m groundwork import-module --in share.json</code> "
        "loads it into another database. Reviews stay private; scheduling restarts fresh. "
        "<span id='status-badge'><a href='/badge.svg'>README badge</a></span> "
        "embeds your live owned count in any README.</p>",
        "<h2 id='status-modular'>Module health</h2>" +
        modularitymod.status_rows() +
        northstarmod.section_html(db_path) +
        toolsmod.section_html(db_path) +
        lettermod.section_html(db_path) +
        blindmod.section_html(db_path) +
        "<h2 id='status-disputes'>Grade disputes</h2>" +
        dismod.queue_html(db_path) +
        storagemod.section_html(db_path) +
        batch5_html() +
        batch6_html(db_path) +
        batch7_html(db_path) +
        batch8_html() +
        batch9_html() + batch10mod.batch10_html() + batch11mod.batch11_html() + batch12mod.batch12_html() +
        "<h2 id='status-api'>Read-only API</h2>"
        "<p><a href='/api/modules.json'>/api/modules.json</a> lists "
        "every module with concept and card counts — the first slice "
        "of a public read API for dashboards. "
        "<span id='status-api-due'><a href='/api/due.json'>"
        "/api/due.json</a> exposes the live due queue.</span></p>",
        "<h2 id='status-sitemap'>Sitemap</h2>"
        "<p><a href='/sitemap.xml'>sitemap.xml</a> lists every page and "
        "module for self-hosters; <a href='/robots.txt'>robots.txt</a> "
        "points crawlers at it.</p>",
        "<h2 id='status-seed'>Groundwork seed</h2>"
        "<p>Groundwork itself is a learnable project: "
        "<code>python3 -m groundwork export-seed --repo PATH --out seed.json</code> "
        "bundles every module under one repo into a portable seed file, and "
        "<code>python3 -m groundwork import-seed --in seed.json</code> "
        "loads it into any database — duplicates skip cleanly, reviews stay private.</p>",
    ])
