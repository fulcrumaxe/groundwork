"""Feature-tour registry: every web-facing item since the MVP, backfilled.

Each entry points at exactly where it is visible in the UI
(page path + element anchor). The /tour catalog and the guided
?tour=<id> banner are both driven by ENTRIES, so a shipped item
with no tour target is a visible gap, not a silent one.
"""

# kind: "mvp" (original loop), "feature" (new capability),
# "improvement" (existing surface made better).
# path may use {mid} (latest module id) and {lesson} (its first
# lesson anchor, e.g. "lesson-add") for module-detail targets.
ENTRIES = [
    # -- MVP baseline: the original learning loop --
    {"id": "due-queue", "kind": "mvp", "title": "Spaced review queue",
     "blurb": "One card at a time, most overdue first. This is the loop.",
     "path": "/due", "anchor": "queue"},
    {"id": "module-library", "kind": "mvp", "title": "Module library",
     "blurb": "Every agent session as a lesson card with owned-progress bars.",
     "path": "/modules", "anchor": "library"},
    {"id": "concept-lessons", "kind": "mvp", "title": "Leveled explainers",
     "blurb": "Each concept explains itself three ways: plain, practitioner, expert.",
     "path": "/modules/{mid}", "anchor": "{lesson}"},
    {"id": "exercise-widgets", "kind": "mvp", "title": "Exercise widgets",
     "blurb": "Parsons drag-and-drop, fill-in blanks, predict-the-output and more.",
     "path": "/modules/{mid}", "anchor": "practice"},
    {"id": "attempt-history", "kind": "mvp", "title": "Attempt history",
     "blurb": "Every try recorded with grade, confidence and timestamp.",
     "path": "/reviews", "anchor": "attempts"},
    {"id": "result-screen", "kind": "mvp", "title": "Honest result screen",
     "blurb": "Answer any card: verdict, feedback, next-due — then back where you came from.",
     "path": "/due", "anchor": "up-next"},
    {"id": "calibration-coach", "kind": "mvp", "title": "Calibration coach",
     "blurb": "Accuracy vs confidence per skill; nudges your overconfident blind spots.",
     "path": "/reviews", "anchor": "calibration"},
    {"id": "mcp-endpoint", "kind": "mvp", "title": "MCP endpoint",
     "blurb": "Agents file learning modules with create_learning_module.",
     "path": "/status", "anchor": "status-mcp"},
    # -- Improvements: the Batch 1 ten --
    {"id": "nav-counts", "kind": "improvement", "title": "Nav badge counts",
     "blurb": "Due, Modules and History counts live in the nav — no guessing.",
     "path": "/", "anchor": "sitenav"},
    {"id": "resume-links", "kind": "improvement", "title": "Resume links",
     "blurb": "Each module card jumps straight to its first unowned lesson.",
     "path": "/modules", "anchor": "resume"},
    {"id": "queue-position", "kind": "improvement", "title": "Queue position",
     "blurb": "Card i of n plus an Up-next tag on the first card.",
     "path": "/due", "anchor": "up-next"},
    {"id": "difficulty-dots", "kind": "improvement", "title": "Difficulty dots",
     "blurb": "Five-dot FSRS difficulty meter on every card. Hover for the number.",
     "path": "/due", "anchor": "difficulty"},
    {"id": "confidence-pills", "kind": "improvement", "title": "Confidence pills",
     "blurb": "Rate 1–5 confidence with every answer; powers the calibration coach.",
     "path": "/due", "anchor": "confidence"},
    {"id": "ctrl-enter", "kind": "improvement", "title": "Ctrl+Enter to submit",
     "blurb": "Submit from any text field with Ctrl/Cmd+Enter. Try it in the box below.",
     "path": "/due", "anchor": "up-next"},
    {"id": "copy-buttons", "kind": "improvement", "title": "Copy buttons",
     "blurb": "Every code block grows a Copy button. Try one in the lesson below.",
     "path": "/modules/{mid}", "anchor": "{lesson}"},
    {"id": "answer-drafts", "kind": "improvement", "title": "Answer drafts",
     "blurb": "Type an answer, reload the page — your text survives. Cleared on submit.",
     "path": "/due", "anchor": "up-next"},
    {"id": "give-up", "kind": "improvement", "title": "Give-up path",
     "blurb": "Stuck? Give up shows the answer and records the lapse honestly.",
     "path": "/due", "anchor": "giveup"},
    {"id": "due-why", "kind": "improvement", "title": "Due-why tooltips",
     "blurb": "Hover why-due: memory strength, days overdue, lapse count.",
     "path": "/due", "anchor": "due-why"},
    # -- Features: the Batch 1 ten --
    {"id": "projects-landing", "kind": "feature", "title": "Projects landing",
     "blurb": "Every repo you are learning, with owned progress — the front door.",
     "path": "/", "anchor": "projects"},
    {"id": "debt-meter", "kind": "feature", "title": "Comprehension debt meter",
     "blurb": "What changed versus what you can prove you own, per repo and file.",
     "path": "/debt", "anchor": "debt-meter"},
    {"id": "diagnose-page", "kind": "feature", "title": "Traceback diagnose page",
     "blurb": "Paste a crash; every function it names links to its lesson.",
     "path": "/diagnose", "anchor": "diagnose-form"},
    {"id": "bloom-ladder", "kind": "feature", "title": "Bloom ladder",
     "blurb": "Six rungs beside each concept; lit rungs mark demonstrated skill tiers.",
     "path": "/modules/{mid}", "anchor": "ladder"},
    {"id": "coverage-timeline", "kind": "feature", "title": "Coverage timeline",
     "blurb": "Every session, what it made, and what stuck.",
     "path": "/reviews", "anchor": "coverage"},
    {"id": "anki-export", "kind": "feature", "title": "Anki export",
     "blurb": "All cards as tab-separated import: front, back, tags.",
     "path": "/modules", "anchor": "exports"},
    {"id": "rss-feed", "kind": "feature", "title": "RSS feed",
     "blurb": "Learning modules as RSS 2.0 for external readers.",
     "path": "/modules", "anchor": "exports"},
    {"id": "module-sharing", "kind": "feature", "title": "Module sharing",
     "blurb": "Export a module to JSON, import it into any Groundwork DB. Reviews stay private.",
     "path": "/status", "anchor": "status-share"},
    {"id": "cli-review", "kind": "feature", "title": "CLI review",
     "blurb": "python3 -m groundwork review — the queue without a browser.",
     "path": "/status", "anchor": "status-cli"},
    {"id": "ci-workflow", "kind": "feature", "title": "CI workflow",
     "blurb": "Tests run on every push; status surfaced below.",
     "path": "/status", "anchor": "status-ci"},
    {"id": "precommit-hook", "kind": "feature", "title": "Pre-commit hook",
     "blurb": "hooks/pre-commit keeps bad commits out; presence shown below.",
     "path": "/status", "anchor": "status-hooks"},
    {"id": "docstring-type", "kind": "feature", "title": "Write-the-docstring exercises",
     "blurb": "Docstring exercise cards render an explanation box. Answer one below.",
     "path": "/due", "anchor": "up-next"},
    # -- Batch 2: Groundwork itself as a learnable project, plus ten more --
    {"id": "seed-modules", "kind": "feature", "title": "Groundwork seed",
     "blurb": "Groundwork itself ships as learnable modules: export one repo's modules to a seed file, import it anywhere.",
     "path": "/status", "anchor": "status-seed"},
    {"id": "relative-times", "kind": "improvement", "title": "Relative timestamps",
     "blurb": "History reads as “just now” and “3h ago” — hover any time for the exact timestamp.",
     "path": "/reviews", "anchor": "timestamps"},
    {"id": "memory-strength", "kind": "improvement", "title": "Memory-strength bars",
     "blurb": "Each Due card shows its FSRS memory strength in days, as a bar.",
     "path": "/due", "anchor": "memory"},
    {"id": "module-sort", "kind": "improvement", "title": "Module sorting",
     "blurb": "The Modules library toggles newest-first and oldest-first.",
     "path": "/modules", "anchor": "sort"},
    {"id": "snooze-card", "kind": "improvement", "title": "Snooze a card",
     "blurb": "Not today? Snooze pushes one card to tomorrow — no grade recorded.",
     "path": "/due", "anchor": "snooze"},
    {"id": "back-to-top", "kind": "improvement", "title": "Back-to-top link",
     "blurb": "Long module pages grow a floating Back to top link.",
     "path": "/modules", "anchor": "top"},
    {"id": "sitemap-robots", "kind": "feature", "title": "Sitemap and robots",
     "blurb": "Every page and module listed for crawlers; see the live map below.",
     "path": "/status", "anchor": "status-sitemap"},
    {"id": "week-review", "kind": "feature", "title": "Week in review",
     "blurb": "Attempts, active days and pass rate for the last 7 days — a weekly ritual.",
     "path": "/reviews", "anchor": "week"},
    {"id": "reviews-csv", "kind": "feature", "title": "Review-log CSV export",
     "blurb": "Every attempt as CSV for personal analysis — grades, confidence, answers.",
     "path": "/status", "anchor": "status-csv"},
    {"id": "readonly-api", "kind": "feature", "title": "Read-only modules API",
     "blurb": "Modules with concept and card counts as JSON, for dashboards.",
     "path": "/status", "anchor": "status-api"},
    {"id": "due-api", "kind": "feature", "title": "Read-only due-queue API",
     "blurb": "The live due queue as JSON — same order as the Due page.",
     "path": "/status", "anchor": "status-api-due"},
    # -- Batch 3: same rhythm, plus the modularity rule --
    {"id": "module-health", "kind": "feature", "title": "Module health",
     "blurb": "Every capability area with its size and ceiling — web.py never grows.",
     "path": "/status", "anchor": "status-modular"},
    {"id": "due-forecast", "kind": "improvement", "title": "Next-gap forecast",
     "blurb": "Each Due card estimates its next gap at steady passes.",
     "path": "/due", "anchor": "forecast"},
    {"id": "queue-chips", "kind": "improvement", "title": "Queue status chips",
     "blurb": "Due, overdue and new cards carry distinct chips in the queue.",
     "path": "/due", "anchor": "queue-status"},
    {"id": "grading-how", "kind": "improvement", "title": "Grading disclosures",
     "blurb": "Every card says how it is judged before you answer.",
     "path": "/due", "anchor": "grading"},
    {"id": "grade-disputes", "kind": "feature", "title": "Grade disputes",
     "blurb": "Flag a wrong reference with one click; maintainers triage the queue.",
     "path": "/status", "anchor": "status-disputes"},
    {"id": "workload-graph", "kind": "feature", "title": "Workload forecast",
     "blurb": "Reviews due per day for the next 30 days — see busy days coming.",
     "path": "/reviews", "anchor": "workload"},
    {"id": "read-times", "kind": "improvement", "title": "Lesson read times",
     "blurb": "The module table of contents estimates minutes per lesson.",
     "path": "/modules/{mid}", "anchor": "readtime"},
    {"id": "module-reset", "kind": "feature", "title": "Module reset",
     "blurb": "Start a module over from a confirm page — lessons stay, progress goes.",
     "path": "/modules/{mid}", "anchor": "reset"},
    {"id": "style-guide", "kind": "feature", "title": "Component gallery",
     "blurb": "Every UI building block on one dev page, with class names.",
     "path": "/styleguide", "anchor": "styleguide"},
    {"id": "shortcuts-cheatsheet", "kind": "improvement", "title": "Keyboard shortcuts",
     "blurb": "g then d jumps to Due, ? opens the cheat sheet — typing never hijacked.",
     "path": "/", "anchor": "shortcuts"},
    {"id": "storage-meter", "kind": "feature", "title": "Storage meter",
     "blurb": "Database size and per-module rows — growth never surprises.",
     "path": "/status", "anchor": "status-storage"},
    # -- Batch 4: ten improvements + ten features, no downsizing --
    {"id": "skip-links", "kind": "improvement", "title": "Skip links",
     "blurb": "Skip to content link plus header/nav/main/footer landmarks.",
     "path": "/", "anchor": "main"},
    {"id": "pretty-404", "kind": "improvement", "title": "Helpful 404",
     "blurb": "Unknown paths get links and a project search, never a bare error.",
     "path": "/404", "anchor": "not-found"},
    {"id": "queue-groups", "kind": "improvement", "title": "Queue grouped by module",
     "blurb": "Due cards gather under collapsible per-module sections.",
     "path": "/due", "anchor": "queue-groups"},
    {"id": "daily-digest", "kind": "improvement", "title": "Daily digest",
     "blurb": "Today at a glance: due now, new cards, and where to start.",
     "path": "/due", "anchor": "digest"},
    {"id": "month-review", "kind": "improvement", "title": "Month in review",
     "blurb": "Concepts owned, accuracy trend and effort across the last 30 days.",
     "path": "/reviews", "anchor": "month"},
    {"id": "related-modules", "kind": "improvement", "title": "Related modules",
     "blurb": "Same repo or shared concepts — keep following the thread.",
     "path": "/modules/{mid}", "anchor": "related"},
    {"id": "decision-quotes", "kind": "improvement", "title": "Decision quotes",
     "blurb": "Agent chose-X-over-Y rationale quoted inside the lesson it shaped.",
     "path": "/modules/{mid}", "anchor": "decisions"},
    {"id": "clarity-votes", "kind": "improvement", "title": "Clarity votes",
     "blurb": "Rate each lesson 1–5; averages feed generation quality.",
     "path": "/modules/{mid}", "anchor": "clarity"},
]

BY_ID = {e["id"]: e for e in ENTRIES}
ORDER = [e["id"] for e in ENTRIES]


def resolve(entry: dict, mid: str = "", lesson: str = "") -> str:
    """Concrete /path#anchor URL for an entry (placeholders filled)."""
    if "{mid}" in entry["path"] and not mid:
        return "/modules"
    path = entry["path"].replace("{mid}", mid).replace("{lesson}", lesson)
    anchor = entry["anchor"].replace("{mid}", mid).replace("{lesson}", lesson)
    return f"{path}#{anchor}" if anchor else path


def step_url(entry_id: str, mid: str = "", lesson: str = "") -> str:
    """Guided-mode URL for one tour step (banner + highlight on arrival)."""
    base = resolve(BY_ID[entry_id], mid, lesson)
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}tour={entry_id}"


def context(entry_id: str, mid: str = "", lesson: str = "") -> dict:
    """Banner data for guided mode: position, title, prev/next step URLs."""
    i = ORDER.index(entry_id)
    prev_url = step_url(ORDER[i - 1], mid, lesson) if i > 0 else "/tour"
    next_url = (step_url(ORDER[i + 1], mid, lesson)
                if i + 1 < len(ORDER) else "/tour")
    entry = BY_ID[entry_id]
    return {"id": entry_id, "index": i + 1, "total": len(ORDER),
            "title": entry["title"], "blurb": entry["blurb"],
            "prev_url": prev_url, "next_url": next_url,
            "kind": entry["kind"]}


def targets(db_path: str) -> tuple[str, str]:
    """(latest module id, its first lesson anchor) for tour deep links."""
    from . import db as dbmod
    from . import lessons as lesmod
    con = dbmod.connect(db_path)
    try:
        m = con.execute(
            "SELECT id FROM modules ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if m is None:
            return "", ""
        mid = m["id"]
        c = con.execute(
            "SELECT id FROM concepts WHERE module_id=? ORDER BY rowid LIMIT 1",
            (mid,)).fetchone()
    finally:
        con.close()
    if c is None:
        return mid, ""
    node = c["id"].split(":", 1)[1] if ":" in c["id"] else c["id"]
    return mid, f"lesson-{lesmod.slug(node)}"


def page_html(db_path: str) -> str:
    """Catalog of every web-facing item, each with a Show-me link."""
    import html
    mid, lesson = targets(db_path)
    parts = ["<p>Every capability below has a visible home. "
             "<b>Show me</b> jumps to it and highlights it; "
             "Prev/Next walks the whole list.</p>",
             f"<p><a class='btn' href='{step_url(ORDER[0], mid, lesson)}'>"
             "Start guided tour</a></p>"]
    groups = (("mvp", "The loop", "The original learning cycle."),
              ("feature", "Features", "New capabilities, Batch 1."),
              ("improvement", "Improvements", "Batch 1 friction removal."))
    n = 0
    for kind, heading, sub in groups:
        items = [e for e in ENTRIES if e["kind"] == kind]
        lis = []
        for e in items:
            n += 1
            url = step_url(e["id"], mid, lesson)
            lis.append(
                f"<li><b>{n}. {html.escape(e['title'])}</b> — "
                f"{html.escape(e['blurb'])} "
                f"<a class='btn' href='{url}'>Show me</a></li>")
        parts.append(
            f"<h2>{heading}</h2><p><small>{sub}</small></p>"
            f"<ol class='tour-steps' start='{n - len(items) + 1}'>"
            + "".join(lis) + "</ol>")
    return "".join(parts)
