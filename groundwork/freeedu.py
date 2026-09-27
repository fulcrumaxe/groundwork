"""Free-forever learner spotlight (F-148): honest AGPL-3.0 banner.

Prominent "free forever for learners" banner for the top of the
History page. Every claim is gated on a live substring probe of the
LICENSE file in this repo: a missing or unrecognized LICENSE renders
"" so caller pages keep legacy bytes. This is the DELTA from Batch 10
licensecheck.py -- that module is a dependency-combining exercise tool
(verdict + reason grading); this module is a learner-facing banner
grounded in the project's own license text.

Caller: history.history_html (one import + one same-line join on the
first parts element, so both branches show it). No DB/schema changes.
Stdlib only (pathlib). ASCII-only strings (repo emoji gate).
"""
from __future__ import annotations

from pathlib import Path

LICENSE_NAME = "LICENSE"
PROJECT_LICENSE = "AGPL-3.0"
STATUS_ANCHOR = "status-b26-freeedu"
BOX_ANCHOR = "freeedu"

# Live-text probes: (fact key, single-line LICENSE substring, cite).
# Single-line needles only: the file wraps mid-sentence, so any needle
# spanning a line break would silently miss. Each banner row renders
# only when its needle is present in the live text.
MARKERS = (
    ("title", "GNU AFFERO GENERAL PUBLIC LICENSE", "LICENSE title"),
    ("version", "Version 3", "LICENSE title"),
    ("free_lic", "is a free, copyleft license", "LICENSE preamble"),
    ("free_all", "software for all its users", "LICENSE preamble"),
    ("run", "permission to run the unmodified Program", "LICENSE sec 2"),
    ("study", "receive source code or can get it", "LICENSE preamble"),
    ("share", "You may convey verbatim copies", "LICENSE sec 4"),
    ("auto", "receives a license from the original licensors",
     "LICENSE sec 10"),
    ("classroom", "may be individuals or organizations", "LICENSE sec 0"),
    ("nofee", "not impose a license fee", "LICENSE sec 10"),
    ("forever", "are irrevocable provided the stated", "LICENSE sec 2"),
    ("duty", "must prominently offer all users", "LICENSE sec 13"),
)

# Banner rows: (row id, required fact keys, fixed line, cite). The line
# is fixed copy; the facts only gate it, so no claim outruns the file.
_ROWS = (
    ("run", ("run",),
     "Run it - unlimited permission to run the unmodified Program",
     "LICENSE sec 2"),
    ("study", ("study",),
     "Study it - you receive source code or can get it",
     "LICENSE preamble"),
    ("share", ("share", "auto"),
     "Share it - convey verbatim copies; every recipient gets a license",
     "LICENSE sec 4, sec 10"),
    ("classroom", ("classroom",),
     "Classrooms included - licensees may be individuals or organizations",
     "LICENSE sec 0"),
    ("nofee", ("nofee",),
     "No fee for these freedoms - no license fee, royalty, or other charge",
     "LICENSE sec 10"),
    ("forever", ("forever",),
     "Forever means irrevocable while you meet its terms",
     "LICENSE sec 2"),
    ("duty", ("duty",),
     "The duty that keeps it free: a modified version run for others "
     "over a network must offer them its source at no charge",
     "LICENSE sec 13"),
)

_LEDE_NEEDS = ("title", "version", "free_lic", "free_all")


def read_license_text(root=None) -> str:
    """Live LICENSE text from the repo root, or "" when unreadable."""
    try:
        base = Path(root) if root else Path(__file__).resolve().parent.parent
        text = (base / LICENSE_NAME).read_text(encoding="utf-8")
        return text if isinstance(text, str) else ""
    except Exception:  # noqa: BLE001 -- probe must never raise
        return ""


def license_facts(text=None) -> dict:
    """Marker hits for LICENSE text; None reads the live file."""
    try:
        if text is None:
            text = read_license_text()
        if not isinstance(text, str) or not text:
            return {"present": False, "recognized": False,
                    **{key: False for key, _, _ in MARKERS}}
        hits = {key: (needle in text) for key, needle, _ in MARKERS}
        hits["present"] = True
        hits["recognized"] = bool(hits["title"] and hits["version"])
        return hits
    except Exception:  # noqa: BLE001 -- facts must never raise
        return {"present": False, "recognized": False,
                **{key: False for key, _, _ in MARKERS}}


def freedoms(facts=None) -> list:
    """Banner rows whose backing markers all held; [] when unrecognized."""
    try:
        facts = license_facts() if facts is None else facts
        if not isinstance(facts, dict) or not facts.get("recognized"):
            return []
        rows = []
        for _rid, needs, line, cite in _ROWS:
            if all(facts.get(k) for k in needs):
                rows.append({"mark": "[x]", "line": line, "cite": cite})
        return rows
    except Exception:  # noqa: BLE001 -- gating must never raise
        return []


def banner_html(license_text=None) -> str:
    """Free-forever spotlight; "" unless the live LICENSE backs it."""
    try:
        facts = license_facts(license_text)
        if not facts.get("recognized"):
            return ""
        if not all(facts.get(k) for k in _LEDE_NEEDS):
            return ""
        rows = freedoms(facts)
        if not rows:
            return ""
        lis = "".join(
            f"<li>{r['mark']} {r['line']} ({r['cite']})</li>" for r in rows)
        return (
            f"<section id='{BOX_ANCHOR}'><h2>Free forever for learners</h2>"
            "<p>Groundwork is free software for every learner and classroom. "
            "Each line below is backed by the live LICENSE file in this repo "
            f"({PROJECT_LICENSE}).</p><ul>{lis}</ul>"
            "<p><small>Plain-language summary, not legal advice. The LICENSE "
            "file is the source of truth - if it goes missing this banner "
            "hides itself.</small></p></section>")
    except Exception:  # noqa: BLE001 -- banner must never raise
        return ""


def tour_entry() -> dict:
    """Tour registry entry for the free-forever spotlight."""
    return {"id": "freeedu-spotlight", "kind": "feature",
            "title": "Free forever for learners",
            "blurb": ("History page spotlights the AGPL-3.0 freedoms for "
                      "learners: run, study, share - every line backed by "
                      "the live LICENSE file."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; facts render from the live LICENSE."""
    facts = license_facts()

    def yn(key: str) -> str:
        return "yes" if facts.get(key) else "no"

    return (
        f"<h3 id='{STATUS_ANCHOR}'>Free forever for learners "
        "<small>(feature)</small></h3>"
        "<p>History page carries a free-forever-for-learners banner: run, "
        "study, share, classrooms included, no fee, irrevocable while terms "
        "are met, plus the network-source duty. Each row renders only when "
        "its sentence is present in the live LICENSE file "
        f"(present: {yn('present')}, AGPL-3.0 title: {yn('title')}, "
        f"no-fee clause: {yn('nofee')}, network duty: {yn('duty')}). "
        "<code>groundwork/freeedu.py</code> provides "
        "<code>license_facts()</code>, <code>freedoms()</code> and "
        "<code>banner_html()</code>, grafted onto "
        "<code>history.history_html</code>; a missing LICENSE renders "
        "nothing.</p>")
