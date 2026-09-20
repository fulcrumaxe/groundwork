"""Batch 3 rule: capabilities live in focused modules; web.py never grows.

AREAS maps each capability area to its module. sizes() reports line
counts, check() enforces the ceilings, and the Status page renders the
table so the rule itself stays visible. Ceilings only ever move down —
except Batch 4's no-downsizing run, where WEB_CEILING covers route
wires only (new logic still lands in area modules). Batch 6 follows
the same exception: delegation lines only, ceiling covers the wires.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

WEB_CEILING = 1112
AREA_CAP = 350

# Capability area -> module implementing it. Batch 3 appends its areas here.
AREAS = {
    "exports": "exports.py",
    "sitemap": "sitemap.py",
    "api": "api.py",
    "cards": "cards.py",
    "lessons": "lessons.py",
    "grading": "grading.py",
    "disputes": "disputes.py",
    "results": "results.py",
    "history": "history.py",
    "workload": "workload.py",
    "ownership": "ownership.py",
    "readtime": "readtime.py",
    "queries": "queries.py",
    "reset": "reset.py",
    "diagnose": "diagnose.py",
    "styleguide": "styleguide.py",
    "shortcuts": "shortcuts.py",
    "debt": "debt.py",
    "status": "status.py",
    "storage": "storage.py",
    "errors": "errors.py",
    "queue": "queue.py",
    "digest": "digest.py",
    "monthreview": "monthreview.py",
    "related": "related.py",
    "decisions": "decisions.py",
    "clarity": "clarity.py",
    "known": "known.py",
    "undo": "undo.py",
    "northstar": "northstar.py",
    "journal": "journal.py",
    "badge": "badge.py",
    "tools": "tools.py",
    "letter": "letter.py",
    "serendipity": "serendipity.py",
    "blindspots": "blindspots.py",
    "bests": "bests.py",
    "titles": "titles.py",
    "empty": "empty.py",
    "palette": "palette.py",
    "copylink": "copylink.py",
    "readprogress": "readprogress.py",
    "charcount": "charcount.py",
    "printcss": "printcss.py",
    "answerguard": "answerguard.py",
    "session": "session.py",
    "garden": "garden.py",
    "cover": "cover.py",
    "filemap": "filemap.py",
    "prereq": "prereq.py",
    "exitticket": "exitticket.py",
    "misconceptions": "misconceptions.py",
    "lessonnotes": "lessonnotes.py",
    "search": "search.py",
    "crumbs": "crumbs.py",
    "levelcarry": "levelcarry.py",
    "tochighlight": "tochighlight.py",
    "cardlinks": "cardlinks.py",
    "pager": "pager.py",
    "footnav": "footnav.py",
    "scrollpos": "scrollpos.py",
    "smell": "smell.py",
    "renameex": "renameex.py",
    "golf": "golf.py",
    "diretro": "diretro.py",
    "errbranch": "errbranch.py",
    "logretro": "logretro.py",
    "typeanno": "typeanno.py",
    "docdoctest": "docdoctest.py",
    "clickcards": "clickcards.py",
    "reviewed": "reviewed.py",
    "modfilter": "modfilter.py",
    "modpages": "modpages.py",
    "chiplinks": "chiplinks.py",
    "recent": "recent.py",
    "unsaved": "unsaved.py",
    "autoscroll": "autoscroll.py",
    "proptest": "proptest.py",
    "fuzztriage": "fuzztriage.py",
    "perffix": "perffix.py",
    "memprofile": "memprofile.py",
    "racehunt": "racehunt.py",
    "deadcode": "deadcode.py",
    "configex": "configex.py",
    "apidesign": "apidesign.py",
}


def sizes() -> dict[str, int]:
    """Line counts for web.py plus every registered area module."""
    out = {"web.py": (ROOT / "web.py").read_text(
        encoding="utf-8").count("\n") + 1}
    for area, rel in AREAS.items():
        out[rel] = (ROOT / rel).read_text(
            encoding="utf-8").count("\n") + 1
    return out


def check() -> list[str]:
    """Ceiling violations; empty means the rule holds."""
    bad = []
    counts = sizes()
    if counts["web.py"] > WEB_CEILING:
        bad.append(f"web.py {counts['web.py']} > {WEB_CEILING}")
    for area, rel in AREAS.items():
        if counts[rel] > AREA_CAP:
            bad.append(f"{rel} {counts[rel]} > {AREA_CAP}")
    return bad


def status_rows() -> str:
    """Status-page table: every area module with its size and ceiling."""
    import html
    counts = sizes()
    over = {b.split()[0] for b in check()}
    rows = "".join(
        f"<tr><td>{html.escape(rel)}</td><td>{counts[rel]}</td>"
        f"<td>{'over' if rel in over else 'ok'}</td></tr>"
        for rel in ["web.py", *AREAS.values()])
    return ("<p>Capabilities live in focused modules; "
            f"web.py stays under {WEB_CEILING} lines, areas under "
            f"{AREA_CAP}.</p>"
            "<table class='log'><tr><th>Module</th><th>Lines</th>"
            f"<th>Ceiling</th></tr>{rows}</table>")
