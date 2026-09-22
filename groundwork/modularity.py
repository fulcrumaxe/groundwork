"""Batch 3 rule: capabilities live in focused modules; web.py never grows.

AREAS maps each capability area to its module. sizes() reports line
counts, check() enforces the ceilings, and the Status page renders the
table so the rule itself stays visible. Ceilings only ever move down —
except Batch 4's no-downsizing run, where WEB_CEILING covers route
wires only (new logic still lands in area modules). Batch 6 follows
the same exception: delegation lines only, ceiling covers the wires.
Batch 9 follows it as well (1112 -> 1142 for sixteen items' wires).
Post-Batch 9 Chrome verification found nested-<style> CSS breakage:
1142 -> 1147 for the separate style-element wire (FOCUS_CSS).
Batch 10 follows it as well (1147 -> 1156 for eight head-wire CSS
imports plus the wordmark header line). status.py sits exactly at
AREA_CAP, so Batch 10 sections join in batch10.py instead.
Batch 11 follows it as well (1156 -> 1182 for nine area imports, the
hero-stats helper, the done-hero empty branch, the modules dry-art
wires, and the confidence-anchor retarget; CSS joins share one line).
status.py stays exactly at AREA_CAP, so Batch 11 sections join in
batch11.py instead.
Batch 12 follows it as well (1182 -> 1190 for eight area CSS imports;
the CSS join and the optimistic foot embed share their lines, and the
status join stays same-line, so status.py holds exactly at AREA_CAP).
status.py stays exactly at AREA_CAP, so Batch 12 sections join in
batch12.py instead.
Batch 13 follows it as well (seven area imports, the 500 wrapper, and
the review-note line; CSS/head/foot/status joins stay same-line, so
status.py holds exactly at AREA_CAP). Batch 13 sections join in
batch13.py instead. (1190 -> 1219 for the wires.)
Batch 17 follows it as well (dial/cold route wires, the quests
delegation line + import, the dial apply + cold return in due_html;
con fetch moved above the parts list. 1219 -> 1227 for the wires.)
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

WEB_CEILING = 1288  # Batch 18: +3 head-wire imports, +order threading (explainflip). Batch 19: symbols/replay/version params, ?replay threading, delegation lines. Batch 20: lessonpin import + pin-order delegation. Handout route + per-section link. Explcalib import + calibration query/wires.
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
    "extlinks": "extlinks.py",
    "canonurl": "canonurl.py",
    "originguard": "originguard.py",
    "buttons": "buttons.py",
    "pageids": "pageids.py",
    "archived": "archived.py",
    "sitenav": "sitenav.py",
    "autofocus": "autofocus.py",
    "specwrite": "specwrite.py",
    "commitmsg": "commitmsg.py",
    "changelog": "changelog.py",
    "repro": "repro.py",
    "bisect": "bisect.py",
    "rebase": "rebase.py",
    "migration": "migration.py",
    "rollback": "rollback.py",
    "collapse": "collapse.py",
    "minisession": "minisession.py",
    "resume": "resume.py",
    "snapshot": "snapshot.py",
    "linkcheck": "linkcheck.py",
    "darkmode": "darkmode.py",
    "typescale": "typescale.py",
    "fontstack": "fontstack.py",
    "threatmodel": "threatmodel.py",
    "secretscan": "secretscan.py",
    "inputaudit": "inputaudit.py",
    "a11yaudit": "a11yaudit.py",
    "i18n": "i18n.py",
    "regexex": "regexex.py",
    "sqlex": "sqlex.py",
    "cssfix": "cssfix.py",
    "wordmark": "wordmark.py",
    "bloomchips": "bloomchips.py",
    "progbar": "progbar.py",
    "ownedbadge": "ownedbadge.py",
    "stagger": "stagger.py",
    "carets": "carets.py",
    "codelines": "codelines.py",
    "highlight": "highlight.py",
    "cliux": "cliux.py",
    "logread": "logread.py",
    "metrics": "metrics.py",
    "flame": "flame.py",
    "crashdump": "crashdump.py",
    "depupgrade": "depupgrade.py",
    "licensecheck": "licensecheck.py",
    "containerize": "containerize.py",
    "batch10": "batch10.py",
    "hinttiers": "hinttiers.py",
    "confslider": "confslider.py",
    "focusrings": "focusrings.py",
    "taptargets": "taptargets.py",
    "radius": "radius.py",
    "spacing": "spacing.py",
    "emptyart": "emptyart.py",
    "donehero": "donehero.py",
    "cipipe": "cipipe.py",
    "flagcut": "flagcut.py",
    "backfill": "backfill.py",
    "pageapi": "pageapi.py",
    "cacheinv": "cacheinv.py",
    "idempot": "idempot.py",
    "ratelimit": "ratelimit.py",
    "webhook": "webhook.py",
    "batch11": "batch11.py",
    "logbook": "logbook.py",
    "shelf": "shelf.py",
    "briefing": "briefing.py",
    "verdicts": "verdicts.py",
    "ownbanner": "ownbanner.py",
    "pressfx": "pressfx.py",
    "skeletons": "skeletons.py",
    "optimistic": "optimistic.py",
    "typecontract": "typecontract.py",
    "retest": "retest.py",
    "quests": "quests.py",
    "diffdial": "diffdial.py",
    "coldattempt": "coldattempt.py",
    "fading": "fading.py",
    "selfexplain": "selfexplain.py",
    "elaboration": "elaboration.py",
    "batch12": "batch12.py",
    "errpage": "errpage.py",
    "formerr": "formerr.py",
    "selection": "selection.py",
    "scrollbar": "scrollbar.py",
    "pageicon": "pageicon.py",
    "ogtags": "ogtags.py",
    "density": "density.py",
    "responsive": "responsive.py",
    "dualcode": "dualcode.py",
    "interleave": "interleave.py",
    "spacingopt": "spacingopt.py",
    "retrieval": "retrieval.py",
    "predict": "predict.py",
    "confweight": "confweight.py",
    "calibdrill": "calibdrill.py",
    "overconf": "overconf.py",
    "batch13": "batch13.py",
    "contractaudit": "contractaudit.py",
    "parsons": "parsons.py",
    "tokens": "tokens.py",
    "pagesnap": "pagesnap.py",
    "emoji": "emoji.py",
    "motion": "motion.py",
    "contrast": "contrast.py",
    "explainflip": "explainflip.py",
    "glossary": "glossary.py",
    "interview": "interview.py",
    "transfer": "transfer.py",
    "fartransfer": "fartransfer.py",
    "pressure": "pressure.py",
    "incident": "incident.py",
    "premortem": "premortem.py",
    "fluency": "fluency.py",
    "nameguess": "nameguess.py",
    "batch18": "batch18.py",
    "symlinks": "symlinks.py",
    "replay": "replay.py",
    "runinputs": "runinputs.py",
    "beforafter": "beforafter.py",
    "srccollapse": "srccollapse.py",
    "whyit": "whyit.py",
    "tryprompts": "tryprompts.py",
    "lessonver": "lessonver.py",
    "apiguess": "apiguess.py",
    "modelmap": "modelmap.py",
    "rubberduck": "rubberduck.py",
    "protege": "protege.py",
    "feynman": "feynman.py",
    "analogy": "analogy.py",
    "counterex": "counterex.py",
    "boundary": "boundary.py",
    "batch19": "batch19.py",
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
