"""Web UI: stdlib HTTP server, server-rendered HTML, no build step.

Every screen asks for an answer before showing one (PRD principle 1).
Routes: / (due queue), /modules/<id> (practice), /reviews (FSRS queue),
POST /cards/<id>/review (grade), POST /mcp (HTTP JSON-RPC).
"""
from __future__ import annotations

import html
import json
import re
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

from . import api as apimod
from . import autofocus as autofocusmod
from . import autoscroll as autoscrollmod
from . import bloomchips as bloomchipsmod
from . import briefing as briefingmod
from . import carets as caretsmod
from . import codelines as codelinesmod
from . import highlight as highlightmod
from . import ownedbadge as ownedbadgemod
from . import progbar as progbarmod
from . import stagger as staggermod
from . import wordmark as wordmarkmod
from . import badge as badgemod
from . import cardlinks as cardlinksmod
from . import cards as cardsmod
from . import chiplinks as chiplinksmod
from . import clarity as claritymod
from . import clickcards as clickcardsmod
from . import collapse as collapsemod
from . import confslider as confslidermod
from . import crumbs as crumbsmod
from . import darkmode as darkmodemod
from . import db as dbmod
from . import debt as debtmod
from . import decisions as decmod
from . import diagnose as diamod
from . import digest as digestmod
from . import disputes as dismod
from . import donehero as doneheromod
from . import emptyart as emptyartmod
from . import errors as errmod
from . import exports as expmod
from . import favicon as faviconmod
from . import fontstack as fontstackmod
from . import focusrings as focusringsmod
from . import footnav as footnavmod
from . import hinttiers as hinttiersmod
from . import history as histmod
from . import journal as journalmod
from . import known as knownmod
from . import lessons as lesmod
from . import levelcarry as levelcarrymod
from . import logbook as logbookmod
from . import mcp as mcplib
from . import minisession as minisessionmod
from . import modfilter as modfiltermod
from . import modpages as modpagesmod
from . import modularity as modularitymod
from . import modules as modmod
from . import optimistic as optimisticmod
from . import ownbanner as ownbannermod
from . import ownership as ownmod
from . import pager as pagermod
from . import palette as palettemod
from . import pressfx as pressfxmod
from . import queries as quemod
from . import radius as radiusmod
from . import queue as qmod
from . import readtime as readtimemod
from . import recent as recentmod
from . import related as relmod
from . import reset as resetmod
from . import results as resmod
from . import resume as resumemod
from . import reviewed as reviewedmod
from . import sched as schedmod
from . import scrollpos as scrollposmod
from . import search as searchmod
from . import serendipity as sermod
from . import session as sessionmod
from . import shelf as shelfmod
from . import shortcuts as shortcutsmod
from . import skeletons as skeletonsmod
from . import sitemap as sitemapmod
from . import sitenav as sitenavmod
from . import snapshot as snapshotmod
from . import spacing as spacingmod
from . import taptargets as taptargetsmod
from . import status as statusmod
from . import storage as storagemod
from . import styleguide as styleguidemod
from . import tochighlight as tochighlightmod
from . import tour as tourmod
from . import typescale as typescalemod
from . import undo as undomod
from . import unsaved as unsavedmod
from . import verdicts as verdictsmod

_SNAPSHOT_SECRET = secrets.token_hex(16)  # Batch 9 I-49: process-lifetime
# share-link secret (links verify while this server process runs).

CSS = ("body{font-family:system-ui,-apple-system,sans-serif;max-width:48rem;"
       "margin:2rem auto;padding:0 1rem;line-height:1.55;color:var(--ink);background:var(--paper)}"
       "nav{margin-bottom:1rem}nav a{margin-right:.25rem}"
       ".skip{position:absolute;left:-999px}.skip:focus{left:.5rem;top:.5rem;"
       "background:var(--paper);padding:.4rem;z-index:9}"
       "h1{font-size:1.6rem}h2{font-size:1.25rem;margin-top:2rem;"
       "border-bottom:2px solid var(--ink);padding-bottom:.25rem}"
       "h3{font-size:1.05rem}h4{font-size:1rem;margin-bottom:.25rem}"
       "h5{font-size:.9rem;margin-bottom:.15rem;color:var(--ink)}"
       "article{border:1px solid #bbb;border-radius:10px;padding:1rem 1.25rem;"
       "margin:1rem 0;background:var(--paper)}"
       "section{margin:1rem 0}"
       "pre{background:#f2f2f2;border:1px solid #ddd;border-radius:6px;"
       "padding:.6rem;overflow:auto;font-size:.85rem}"
       "blockquote{border-left:3px solid #666;margin:.5rem 0;padding:.25rem .75rem;"
       "color:#333;background:#fafafa}"
       "button{background:#1a1a1a;color:#fff;border:none;border-radius:6px;"
       "padding:.45rem .9rem;margin:.2rem;cursor:pointer;font-size:.9rem}"
       "button:hover{background:#333}"
       "input,select,textarea{border:1px solid #999;border-radius:6px;"
       "padding:.4rem;font-size:.9rem;margin:.15rem;color:var(--ink);background:var(--paper)}"
       "textarea{width:100%;max-width:100%;box-sizing:border-box}"
       "table{border-collapse:collapse;margin:.5rem 0}"
       "td,th{border:1px solid #ccc;padding:.35rem .6rem;text-align:left}"
       "details{margin:.4rem 0}summary{cursor:pointer;font-weight:600}"
       "ol li{margin:.15rem 0}"
       ".stale{color:#a00;font-weight:bold}.ok{color:#0a0}"
       ".unstated{color:#666}"
       "body[data-page=due]{--accent:#b3541e}"
       "body[data-page=modules]{--accent:#1f6f5c}"
       "body[data-page=history]{--accent:#3d5a80}"
       "body[data-page=debt]{--accent:#8c2f2f}"
       "body[data-page=tour]{--accent:#1a1a1a}"
       "body[data-page=status]{--accent:#555}"
       "header.page-head{border-bottom:3px solid var(--accent,#1a1a1a);"
       "padding-bottom:.5rem;margin-bottom:1rem}"
       "header.page-head h1{margin:.4rem 0 .2rem}"
       ".lede{color:var(--stale);margin:.1rem 0 .5rem}"
       "nav a{padding:.2rem .5rem;border-radius:6px;text-decoration:none;color:var(--ink)}"
       "nav a[aria-current=page]{background:#1a1a1a;color:#fff}"
       ".crumbs{font-size:.85rem;color:var(--stale);margin:.5rem 0}"
       ".crumbs a{color:inherit}"
       ".modcard{display:block;border:1px solid #bbb;border-radius:10px;"
       "padding:.75rem 1rem;margin:.75rem 0;text-decoration:none;color:inherit;background:var(--paper)}"
       ".modcard:hover{border-color:var(--accent,#1a1a1a)}"
       ".modcard h3{margin:.1rem 0}"
       ".modcard small{color:var(--stale)}"
       ".chip{display:inline-block;font-size:.75rem;border:1px solid #999;"
       "border-radius:999px;padding:.05rem .5rem;margin-right:.25rem;color:var(--ink)}"
       ".bar{height:.5rem;background:#e6e6e6;border-radius:4px;overflow:hidden;margin:.4rem 0}"
       ".bar i{display:block;height:100%;background:var(--accent,#1a1a1a)}"
       "table.log{width:100%}"
       "footer.page-foot{margin-top:2rem;padding-top:.75rem;border-top:1px solid #ddd;"
       "font-size:.85rem;color:var(--stale)}"
       "html{scroll-behavior:smooth}"
       "@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}"
       "article.next{border:2px solid var(--accent,#1a1a1a)}"
       ".next-tag{font-weight:700;color:var(--accent,#1a1a1a);margin:.2rem 0}"
       "p.toc{position:sticky;top:0;background:var(--paper);padding:.4rem 0;"
       "border-bottom:1px solid #ddd;z-index:1}"
       ".verdict{font-size:1.15rem;font-weight:700}"
       "ol.parsons{padding-left:1.2rem}"
       "ol.parsons li{cursor:grab;border:1px solid #ddd;border-radius:6px;"
       "padding:.25rem .5rem;margin:.25rem 0;background:#fafafa}"
       ".grip{color:#666;margin-right:.3rem}"
       ".conf-group{white-space:nowrap}"
       ".conf{display:inline-block;border:1px solid #999;border-radius:999px;"
       "padding:.05rem .45rem;margin:.1rem;cursor:pointer;font-size:.85rem}"
       ".conf input{accent-color:#1a1a1a;margin-right:.2rem}"
       ".codewrap{position:relative}"
       "button.giveup{background:none;color:var(--stale);text-decoration:underline;"
       "padding:.2rem;font-size:.85rem}"
       "button.giveup:hover{background:none;color:var(--ink)}"
       ".ladder{display:inline-flex;align-items:flex-end;gap:2px;margin-left:.4rem}"
       ".ladder i{width:8px;background:#ddd;border-radius:2px}"
       ".ladder i.on{background:var(--accent,#1a1a1a)}"
       ".copybtn{position:absolute;top:.3rem;right:.3rem;font-size:.75rem;"
       "padding:.2rem .5rem}"
       "a{color:var(--accent,#1a1a1a)}"
       "a:visited{color:var(--accent,#1a1a1a)}"
       "nav a:visited{color:var(--ink)}"
       "nav a[aria-current=page]:visited{color:#fff}"
       "a.btn{display:inline-block;background:#1a1a1a;color:#fff;"
       "border-radius:6px;padding:.45rem .9rem;margin:.2rem;"
       "text-decoration:none;font-size:.9rem}"
       "a.btn:hover{background:#333}"
       "a.btn:visited{color:#fff}"
       ":target{outline:3px solid var(--accent,#1a1a1a);outline-offset:3px}"
       ".tour-banner{border:2px solid var(--accent,#1a1a1a);border-radius:10px;"
       "padding:.6rem .9rem;margin:0 0 1rem;background:var(--paper)}"
       ".tour-banner small{color:var(--stale)}"
       ".tour-steps{list-style:none;padding-left:0}"
       ".tour-steps li{margin:.6rem 0}"
       ".status-ok{color:#0a0;font-weight:700}"
       ".status-missing{color:#a00;font-weight:700}"
       "a.totop{position:fixed;bottom:1rem;right:1rem;background:#1a1a1a;"
       "color:#fff;border-radius:999px;padding:.5rem .9rem;font-size:.85rem;"
       "text-decoration:none}"
       "a.totop:visited{color:#fff}"
       "a.totop:hover{background:#333}"
       "#shortcuts{position:fixed;bottom:1rem;left:1rem;background:#fff;"
       "border:2px solid #1a1a1a;border-radius:10px;padding:.5rem 1rem;"
       "max-width:22rem;box-shadow:0 4px 16px rgba(0,0,0,.25)}"
       "kbd{border:1px solid #999;border-radius:4px;padding:0 .3rem;"
       "background:#f4f4f4;font-size:.8rem}")

# Batch 7 I-16: focus_css() returns a complete <style> element (see
# clickcards.focus_css + tests/test_clickcards.py), so it must NOT be
# concatenated into CSS (that nests <style> inside <style>, closes the
# head stylesheet early, and dumps all later CSS into <body> as text).
FOCUS_CSS = clickcardsmod.focus_css()
CSS += palettemod.palette_css() + darkmodemod.dark_css() + typescalemod.scale_css() + fontstackmod.stack_css() + wordmarkmod.wordmark_css() + bloomchipsmod.chip_css() + progbarmod.progbar_css() + ownedbadgemod.badge_css() + staggermod.stagger_css() + caretsmod.carets_css() + codelinesmod.codelines_css() + highlightmod.highlight_css() + hinttiersmod.hinttiers_css() + confslidermod.css() + focusringsmod.css() + taptargetsmod.target_css() + radiusmod.radius_css() + spacingmod.spacing_css() + doneheromod.hero_css() + logbookmod.logbook_css() + shelfmod.shelf_css() + briefingmod.briefing_css() + verdictsmod.verdicts_css() + ownbannermod.ownbanner_css() + pressfxmod.pressfx_css() + skeletonsmod.skeletons_css() + optimisticmod.optimistic_css()  # Batch 9 I-51/52/53/54: token variables, dark overrides, type scale, font stacks. Batch 10 I-55..I-62: wordmark, bloom chips, progress motion, owned badge, stagger, carets, code lines, highlight. Batch 11 I-63..I-70: hint tiers, confidence segments, focus rings, tap floor, radii, spacing, hero. Batch 12 I-71..I-73/I-77/I-79..I-82: logbook, shelf, briefing, verdicts, banner, press, skeletons, optimistic submit.

GLOBAL_JS = """
<script>
(function () {
  // Ctrl/Cmd+Enter submits from any text field (choice-button forms
  // keep their click-to-answer behavior; radios are ignored).
  document.addEventListener('keydown', function (e) {
    if (!(e.ctrlKey || e.metaKey) || e.key !== 'Enter') return;
    var t = e.target;
    var textual = t && (t.tagName === 'TEXTAREA' ||
      (t.tagName === 'INPUT' && t.type === 'text'));
    if (!textual) return;
    var f = t.closest('form');
    if (f) { e.preventDefault(); f.submit(); }
  });
  // Copy buttons on every code block.
  if (navigator.clipboard) {
    Array.prototype.forEach.call(document.querySelectorAll('pre'), function (pre) {
      if (pre.parentElement.classList.contains('codewrap')) return;
      var w = document.createElement('div');
      w.className = 'codewrap';
      pre.parentNode.insertBefore(w, pre);
      w.appendChild(pre);
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'copybtn'; b.textContent = 'Copy';
      b.addEventListener('click', function () {
        navigator.clipboard.writeText(pre.innerText).then(function () {
          b.textContent = 'Copied';
          setTimeout(function () { b.textContent = 'Copy'; }, 1500);
        });
      });
      w.appendChild(b);
    });
  }
  // Draft preservation: text answers survive reloads; cleared on submit.
  Array.prototype.forEach.call(
    document.querySelectorAll('form[action^="/cards/"]'), function (f) {
    var key = 'gw-draft:' + f.getAttribute('action');
    var fields = Array.prototype.filter.call(
      f.querySelectorAll('textarea, input'),
      function (el) { return el.tagName === 'TEXTAREA' || el.type === 'text'; });
    var saved = {};
    try { saved = JSON.parse(localStorage.getItem(key) || '{}'); } catch (e) {}
    fields.forEach(function (el) {
      if (el.name && saved[el.name] !== undefined) el.value = saved[el.name];
      el.addEventListener('input', function () {
        var cur = {};
        try { cur = JSON.parse(localStorage.getItem(key) || '{}'); } catch (e) {}
        cur[el.name] = el.value;
        try { localStorage.setItem(key, JSON.stringify(cur)); } catch (e) {}
      });
    });
    f.addEventListener('submit', function () {
      try { localStorage.removeItem(key); } catch (e) {}
    });
  });
})();
</script>"""





# Single source of truth lives in groundwork/sitenav.py (I-39);
# web.NAV stays as the alias existing callers import.
NAV = sitenavmod.NAV


def _safe_origin(value: str) -> str:
    """Keep only same-site page paths; fall back to the Due queue."""
    v = (value or "/").strip()
    if (v.startswith("/") and not v.startswith("//")
            and "\\" not in v
            and not any(ch.isspace() or ch in "\"'<>`" for ch in v)):
        return v
    return "/"


def page(title: str, body: str, active: str = "projects",
         page_id: str = "projects", lede: str = "",
         counts: dict | None = None, tour: dict | None = None) -> bytes:
    # Header nav renders from the single sitenav table (I-39).
    links = sitenavmod.header_nav(active, counts)
    head = (f"<a class='skip' href='#main'>Skip to content</a>"
            f"<header class='page-head' id='top'><nav id='sitenav'>{links}</nav>"
            f"<h1>{wordmarkmod.wordmark_svg()} {html.escape(title)}</h1>{searchmod.header_html()}")
    if lede:
        head += f"<p class='lede'>{html.escape(lede)}</p>"
    head += "</header>"
    banner = ""
    if tour:
        banner = (
            f"<p class='tour-banner'><small>Tour {tour['index']} of "
            f"{tour['total']} · {html.escape(tour['kind'])}</small><br>"
            f"<b>{html.escape(tour['title'])}</b> — "
            f"{html.escape(tour['blurb'])}<br>"
            f"<a class='btn' href='{tour['prev_url']}'>‹ Prev</a> "
            f"<a class='btn' href='{tour['next_url']}'>Next ›</a> "
            f"<a href='/tour'>Exit tour</a></p>")
    foot = footnavmod.footer(sitenavmod.href_of(active))
    body = banner + body
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style>"
            f"{FOCUS_CSS}</head>"
            f"<body data-page='{page_id}'>{head}<main id='main'>{body}</main>{foot}"
            f"{shortcutsmod.overlay_html()}{GLOBAL_JS}{shortcutsmod.script_js()}"
            f"{searchmod.script_js()}{scrollposmod.record_js()}"
            f"{reviewedmod.script_js()}{unsavedmod.guard_js()}{autofocusmod.focus_js()}"
            f"{collapsemod.collapse_js()}{optimisticmod.optimistic_js()}</body></html>").encode()


def _first_unowned(owned: dict, cids_in_order: list[str]) -> str | None:
    """First concept id in module order that is not Owned (resume target)."""
    for cid in cids_in_order:
        _, is_owned = owned.get(cid, (0, False))
        if not is_owned:
            return cid
    return None


def _concept_status(stale: bool, attempts: int, owned: bool) -> str:
    """One-word learning state for a concept chip."""
    if stale:
        return "Stale"
    if owned:
        return "Owned"
    if attempts == 0:
        return "New"
    return "Learning"


def _parse_review_form(raw: str) -> tuple[str, int, str]:
    """Split a card-review POST body into (answer, confidence, origin)."""
    form = parse_qs(raw, keep_blank_values=True)
    bkeys = sorted([k for k in form if k.startswith("b") and k[1:].isdigit()],
                   key=lambda k: int(k[1:]))
    skeys = sorted([k for k in form if k.startswith("s") and k[1:].isdigit()],
                   key=lambda k: int(k[1:]))
    mkeys = sorted([k for k in form if k.startswith("m") and k[1:].isdigit()],
                   key=lambda k: int(k[1:]))
    if bkeys:
        answer = "\n".join(f"{k[1:]}={form[k][0]}" for k in bkeys)
    elif skeys:
        answer = "\n".join(form[k][0] for k in skeys)
    elif mkeys:
        answer = "\n".join(f"{k[1:]}={form[k][0]}" for k in mkeys)
    else:
        # Choice buttons and the typed input share the name; the
        # button click wins, typed text is the fallback. Parsons
        # posts the drag order in `answer`, numbers in `answer_text`.
        vals = [v for v in form.get("answer", [""]) if v.strip()]
        answer = vals[-1] if vals else form.get("answer_text", [""])[0]
    conf = form.get("confidence", ["3"])[0]
    try:
        conf_i = int(conf)
    except ValueError:
        conf_i = 3
    origin = _safe_origin((form.get("origin", ["/due"]) or ["/due"])[0])
    return answer, conf_i, origin

class Handler(BaseHTTPRequestHandler):
    db_path = "groundwork.db"

    def log_message(self, *a):
        pass

    # -- helpers
    def _send(self, data: bytes, code: int = 200, ctype: str = "text/html"):
        if ctype == "text/html" and getattr(self, "_level", "auto") != "auto":
            data = levelcarrymod.carry_html(data.decode(), self._level).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _con(self):
        return dbmod.connect(self.db_path)

    def _nav_counts(self) -> dict:
        """Nav badge counts: due cards, modules, lifetime attempts."""
        from . import sched as schedmod
        now = schedmod.iso(schedmod.utcnow())
        con = self._con()
        try:
            due = con.execute(
                "SELECT COUNT(*) FROM cards WHERE due <= ? AND stale = 0",
                (now,)).fetchone()[0]
            mods = con.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
            tries = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        finally:
            con.close()
        return {"due": due, "modules": mods, "history": tries}

    # -- GET
    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        level = levelcarrymod.normalize(query.get("level", ["auto"])[0])
        self._level = level
        counts = self._nav_counts()
        tour_ctx = None
        tour_id = query.get("tour", [""])[0]
        if tour_id in tourmod.BY_ID:
            mid, lesson = tourmod.targets(self.db_path)
            tour_ctx = tourmod.context(tour_id, mid, lesson)
        if url.path == "/":
            self._send(page("Projects", self.projects_html(),
                            active="projects", page_id="projects",
                            lede="Every repo you are learning — pick one and study it.",
                            counts=counts, tour=tour_ctx))
        elif url.path == "/due":
            one = query.get("mode", [""])[0] == "one"
            resume_key = query.get("resume", [""])[0]
            self._send(page("Due", self.due_html(level, one, resume_key),
                            active="due", page_id="due",
                            lede="What to practice next — your spaced queue, one card at a time.",
                            counts=counts, tour=tour_ctx))
        elif url.path == "/reviews":
            self._send(page("History", self.history_html(),
                            active="history", page_id="history",
                            lede="What you have practiced — every attempt, grade and calibration.",
                            counts=counts, tour=tour_ctx))
        elif url.path == "/modules":
            repo = query.get("repo", [""])[0]
            sort = query.get("sort", ["newest"])[0]
            status = query.get("status", ["all"])[0]
            page_num = query.get("page", ["1"])[0]
            lede = (f"Modules in {repo} — pick one and study it." if repo
                    else "Every agent session as a lesson — pick one and study it.")
            self._send(page("Modules", self.modules_html(repo, sort, status, page_num),
                            active="modules", page_id="modules",
                            lede=lede, counts=counts, tour=tour_ctx))
        elif url.path == "/debt":
            self._send(page("Debt", self.debt_html(),
                            active="debt", page_id="debt",
                            lede="What changed versus what you can prove — pay it down.",
                            counts=counts, tour=tour_ctx))
        elif url.path == "/diagnose":
            self._send(page("Diagnose", diamod.diagnose_html(self.db_path),
                            active="due", page_id="due",
                            lede="Paste a traceback — study first, then fix.",
                            counts=counts, tour=tour_ctx))
        elif url.path == "/styleguide":
            self._send(page("Styleguide", styleguidemod.page(),
                            active="tour", page_id="tour",
                            lede="Every component, one gallery.",
                            counts=counts, tour=tour_ctx))
        elif url.path == "/tour":
            self._send(page("Tour", self.tour_html(),
                            active="tour", page_id="tour",
                            lede="Every capability, each with a visible home.",
                            counts=counts, tour=tour_ctx))
        elif url.path == "/status":
            self._send(page("Status", self.status_html(),
                            active="tour", page_id="status",
                            lede="Machine-room items with no page of their own.",
                            counts=counts, tour=tour_ctx))
        elif url.path == "/journal":
            self._send(page("Journal", self.journal_html(),
                            active="tour", page_id="journal",
                            lede="What did you misjudge this week? Private by design.",
                            counts=counts, tour=tour_ctx))
        elif url.path == "/search":
            q = query.get("q", [""])[0]
            self._send(page("Search", self.search_html(q),
                            active="projects", page_id="projects",
                            lede="Concepts, modules, and symbols — ranked.",
                            counts=counts, tour=tour_ctx))
        elif url.path == "/export/anki.tsv":
            self._send(self.anki_tsv().encode(), 200,
                       "text/tab-separated-values; charset=utf-8")
        elif url.path == "/export/reviews.csv":
            self._send(self.reviews_csv().encode(), 200,
                       "text/csv; charset=utf-8")
        elif url.path == "/export/me.json":
            self._send(self.me_json().encode(), 200,
                       "application/json; charset=utf-8")
        elif url.path == "/api/modules.json":
            self._send(self.api_modules().encode(), 200,
                       "application/json; charset=utf-8")
        elif url.path == "/api/due.json":
            self._send(self.api_due().encode(), 200,
                       "application/json; charset=utf-8")
        elif url.path == "/badge.svg":
            self._send(self.badge_svg().encode(), 200,
                       "image/svg+xml; charset=utf-8")
        elif url.path == "/favicon.ico":
            self._send(self.favicon_svg().encode(), 200,
                       "image/svg+xml; charset=utf-8")
        elif url.path == "/feed.xml":
            host = self.headers.get("Host", "127.0.0.1:8765")
            self._send(self.feed_xml(f"http://{host}").encode(), 200,
                       "application/rss+xml; charset=utf-8")
        elif url.path == "/sitemap.xml":
            host = self.headers.get("Host", "127.0.0.1:8765")
            self._send(self.sitemap_xml(f"http://{host}").encode(), 200,
                       "application/xml; charset=utf-8")
        elif url.path.startswith("/share/"):
            snap = snapshotmod.decode_snapshot(url.path[len("/share/"):],
                                               _SNAPSHOT_SECRET)
            if snap is None:
                self._send(page("Not found",
                                errmod.not_found_html(url.path),
                                counts=counts, tour=tour_ctx), 404)
            else:
                self._send(page("Shared session",
                                snapshotmod.snapshot_html(snap),
                                active="tour", page_id="tour",
                                counts=counts, tour=tour_ctx))
            return
        elif url.path == "/robots.txt":
            host = self.headers.get("Host", "127.0.0.1:8765")
            self._send(self.robots_txt(f"http://{host}").encode(), 200,
                       "text/plain; charset=utf-8")
        elif url.path.startswith("/modules/") and url.path.endswith("/reset"):
            mid = url.path.split("/")[2]
            con = self._con()
            try:
                m = con.execute("SELECT task_summary FROM modules WHERE id=?",
                                (mid,)).fetchone()
            finally:
                con.close()
            if m is None:
                self._send(page("Not found", errmod.not_found_html(
                    url.path, "Unknown module."), active="modules",
                    page_id="modules", counts=counts, tour=tour_ctx), 404)
            else:
                self._send(page("Reset", resetmod.confirm_html(
                    mid, m["task_summary"]), active="modules",
                    page_id="modules", counts=counts, tour=tour_ctx))
        elif url.path.startswith("/modules/"):
            mid = url.path.split("/")[-1]
            body = self.module_html(mid, level)
            if body == "<p>Unknown module.</p>":
                self._send(page("Not found", errmod.not_found_html(
                    url.path, "Unknown module."), active="modules",
                    page_id="modules", counts=counts, tour=tour_ctx), 404)
            else:
                self._send(page("Module", body, active="modules",
                                page_id="modules", counts=counts,
                                tour=tour_ctx))
        else:
            self._send(page("Not found",
                            errmod.not_found_html(url.path),
                            counts=counts, tour=tour_ctx), 404)

    def _hero_stats(self) -> dict:
        """Today's answered/accuracy plus the next due date for the hero."""
        con = self._con()
        try:
            today = schedmod.utcnow().strftime("%Y-%m-%d")
            grades = [r[0] for r in con.execute(
                "SELECT grade FROM reviews WHERE substr(reviewed_at, 1, 10)=?",
                (today,)).fetchall()]
            nxt = con.execute("SELECT MIN(due) FROM cards").fetchone()
        finally:
            con.close()
        summary = sessionmod.summarize([{"grade": g} for g in grades])
        summary["next_due"] = nxt[0] if nxt and nxt[0] else ""
        return summary

    def due_html(self, level: str = "auto", one: bool = False,
                 resume_key: str = "") -> str:
        server = mcplib.MCPServer(self.db_path)
        due = server.tool_list_due_reviews({"limit": 20})["due"]
        due = resumemod.session_cards(due, resume_key or "")
        parts = [digestmod.section_html(self.db_path),
                 recentmod.strip_html(),
                 minisessionmod.session_box_html(due),
                 resumemod.resume_box_html(resume_key or "", len(due))]
        if one and due:
            due = due[:1]
            parts.append("<p id='one-card-note'>One card is enough today — "
                         "no guilt. <a id='one-card' href='/due'>Full queue</a></p>")
        else:
            parts.append("<p><a id='one-card' href='/due?mode=one'>"
                         "Just one card</a> for low-energy days.</p>")
        parts.append(sermod.section_html(self.db_path))
        if not due:
            stats = self._hero_stats()
            parts.append(doneheromod.done_hero_html(
                stats["answered"], stats["accuracy"], stats["next_due"]))
        con2 = self._con()
        try:
            study = quemod.stored_lessons(con2, [c["id"] for c in due])
            tries = quemod.attempts(con2, [c["id"] for c in due])
        finally:
            con2.close()
        grouped = qmod.groups(self.db_path, due)
        n = 0
        for gi, g in enumerate(grouped):
            mark = " id='queue-groups'" if gi == 0 else ""
            nc = len(g["cards"])
            parts.append(
                f"<details open><summary{mark}>"
                f"{html.escape(g['title'])} — {nc} card{'s' if nc != 1 else ''}"
                f" (<a href='/modules/{g['mid']}'>study</a>)</summary>")
            for c in g["cards"]:
                i = n
                n += 1
                stale = (" <span class='stale'>[stale]</span>"
                         if c.get("stale") else "")
                if c["id"] in study:
                    lesson_dict, mastery = study[c["id"]]
                    explainer = lesmod.render_levels(
                        lesson_dict, mastery, tries.get(c["id"], 0), level, "/")
                    lesson = (f"<details><summary>Study first — explained your way</summary>"
                              f"{explainer}</details>")
                else:
                    lesson = ""
                first = (i == 0)
                tag = ("<p class='next-tag' id='up-next'>Up next</p>"
                       if first else "")
                cls = " class='next'" if first else ""
                pos = f"<p><small>Card {i + 1} of {len(due)}</small></p>"
                dots = cardsmod._difficulty_dots(
                    c.get("difficulty"), " id='difficulty'" if first else "")
                widget = cardsmod.answer_widget(c, tries.get(c["id"], 0), "/due")
                why_extra = ""
                if first:
                    # Stable tour anchors on the lead card only.
                    why_extra = " id='due-why'"
                    widget = widget.replace(
                        "<fieldset class='confslider'>",
                        "<fieldset class='confslider' id='confidence'>", 1)
                    widget = widget.replace(
                        "<button class='giveup'>",
                        "<button class='giveup' id='giveup'>", 1)
                    widget = widget.replace("<details><summary>How grading works</summary>", "<details id='grading'><summary>How grading works</summary>", 1)
                mem = cardsmod._memory_bar(c, " id='memory'" if first else "")
                forecast = cardsmod.forecast_html(c, " id='forecast'" if first else "")
                chip = cardsmod.status_chip(c, tries.get(c["id"], 0), " id='queue-status'" if first else "")
                snooze_id = " id='snooze'" if first else ""
                snooze = (
                    f"<form method='post' action='/cards/{c['id']}/snooze'>"
                    f"<input type='hidden' name='origin' value='/due'>"
                    f"<button{snooze_id}>Snooze until tomorrow</button></form>")
                parts.append(
                    f"<article{cls} id='{scrollposmod.card_anchor(c['id'])}'>"
                    f"{tag}{pos}{cardsmod._due_why(c, why_extra)}"
                    f"<h3>{html.escape(c.get('concept', ''))}{stale} {dots} {chip} {cardsmod.bloom_chip(c)}</h3>"
                    f"{mem}{forecast}{lesson}"
                    f"{lesmod.why_html(c)}"
                    f"<p>{html.escape(c.get('front', ''))}</p>"
                    f"{widget}{snooze}</article>")
            parts.append("</details>")
        parts.append("<p><a class='btn' href='/modules'>Browse all modules</a> "
                     "<a class='btn' href='/reviews'>Review history</a> "
                     "<a class='btn' href='/diagnose'>Diagnose a traceback</a></p>")
        return "<div id='queue'>" + "".join(parts) + "</div>"

    def history_html(self) -> str:
        return histmod.history_html(self.db_path)

    # Thin delegation: the real renderers live in focused modules
    # per the Batch 3 modularity rule (exports, api, sitemap,
    # cards, lessons, history, ownership, ...).
    def anki_tsv(self) -> str:
        return expmod.anki_tsv(self.db_path)

    def api_modules(self) -> str:
        return apimod.modules_json(self.db_path)

    def api_due(self) -> str:
        return apimod.due_json(self.db_path)

    def search_html(self, q: str) -> str:
        """Ranked header-search hits over modules, concepts, symbols."""
        con = self._con()
        try:
            mods = con.execute("SELECT id, task_summary FROM modules").fetchall()
            cons = con.execute(
                "SELECT id, module_id, name, kind FROM concepts").fetchall()
        finally:
            con.close()
        recs = (searchmod.modules_to_records(mods)
                + searchmod.concepts_to_records(cons))
        return searchmod.results_html(searchmod.search(recs, q), q)

    def reviews_csv(self) -> str:
        return expmod.reviews_csv(self.db_path)

    def me_json(self) -> str:
        return expmod.personal_json(self.db_path)

    def badge_svg(self) -> str:
        return badgemod.badge_svg(self.db_path)

    def favicon_svg(self) -> str:
        return faviconmod.favicon_svg()

    def feed_xml(self, base_url: str) -> str:
        return expmod.feed_xml(self.db_path, base_url)

    def sitemap_xml(self, base_url: str) -> str:
        return sitemapmod.sitemap_xml(self.db_path, base_url)

    def robots_txt(self, base_url: str) -> str:
        return sitemapmod.robots_txt(base_url)

    def debt_html(self) -> str:
        return debtmod.debt_html(self.db_path)

    def projects_html(self) -> str:
        """Projects landing: every repo with modules, newest activity first."""
        con = self._con()
        try:
            mods = con.execute(
                "SELECT id, repo, task_summary, created_at FROM modules"
                " ORDER BY created_at DESC").fetchall()
            stats: dict[str, list] = {}
            for m in mods:
                omap = ownmod.owned_map(con, m["id"])
                cell = stats.setdefault(m["repo"] or "(unknown)", [0, 0, 0, ""])
                cell[0] += 1
                cell[1] += sum(1 for _, o in omap.values() if o)
                cell[2] += len(omap)
                cell[3] = cell[3] or (m["created_at"] or "")[:10]
        finally:
            con.close()
        if not mods:
            return ("<p>No projects yet. Finish an agent session with the "
                    "`create_learning_module` MCP tool and its repo appears here.</p>")
        parts = ["<div id='projects'>"]
        order = sorted(stats, key=lambda r: stats[r][3], reverse=True)
        for repo in order:
            n_mods, owned_n, total_n, _ = stats[repo]
            pct = int(round(100 * owned_n / total_n)) if total_n else 0
            parts.append(
                f"<a class='modcard' href='/modules?repo={quote(repo, safe='')}'"
                f" title='{html.escape(repo)}'>"
                f"<h3>{html.escape(repo.rstrip('/').split('/')[-1] or repo)}</h3>"
                f"<small>{html.escape(repo)}</small>"
                f"<div class='bar' aria-hidden='true'><i style='width:{pct}%'></i></div>"
                f"<p><small>{n_mods} module{'s' if n_mods != 1 else ''} · "
                f"{owned_n}/{total_n} concepts owned</small></p></a>")
        parts.append("</div>")
        return "".join(parts)

    def modules_html(self, repo: str = "", sort: str = "newest",
                     status: str = "all", page=1) -> str:
        """The library: every MCP session as a module card with progress."""
        if sort not in ("newest", "oldest"):
            sort = "newest"
        status = modfiltermod.normalize(status)
        con = self._con()
        try:
            mods = con.execute(
                "SELECT id, task_summary, created_at, repo, commit_range FROM modules"
                " ORDER BY created_at DESC, rowid DESC").fetchall()
            cards = []
            for m in mods:
                stats = con.execute(
                    "SELECT COUNT(*) AS n,"
                    " SUM(cards.stale) AS stale FROM concepts"
                    " LEFT JOIN cards ON cards.concept_id = concepts.id"
                    " WHERE concepts.module_id=?", (m["id"],)).fetchone()
                omap = ownmod.owned_map(con, m["id"])
                order = [r[0] for r in con.execute(
                    "SELECT id FROM concepts WHERE module_id=? ORDER BY rowid",
                    (m["id"],)).fetchall()]
                cards.append((m, stats, omap, order))
        finally:
            con.close()
        if repo:
            cards = [c for c in cards if (c[0]["repo"] or "") == repo]
        if not cards:
            if repo:
                return (f"<p class='crumbs'><a href='/'>Projects</a> › "
                        f"{html.escape(repo)}</p>"
                        + emptyartmod.art_for("modules") +
                        "<p>No modules for this project yet.</p>")
            return (emptyartmod.art_for("modules") +
                    "<p>No modules yet. Finish an agent session with the "
                    "`create_learning_module` MCP tool and it appears here.</p>")
        if sort == "oldest":
            cards = cards[::-1]
        enriched = []
        for (m, stats, omap, order) in cards:
            owned_n = sum(1 for _, o in omap.values() if o)
            enriched.append((m, stats, omap, order, owned_n, len(omap),
                             stats["stale"] or 0))
        rows = [{"id": m["id"], "owned": owned_n, "total": total, "stale": stale}
                for (m, _s, _o, _ord, owned_n, total, stale) in enriched]
        parts = []
        if repo:
            parts.append(f"<p class='crumbs'><a href='/'>Projects</a> › "
                         f"{html.escape(repo)}</p>")
        other = "oldest" if sort == "newest" else "newest"
        qs = (f"?sort={other}"
              + (f"&repo={quote(repo, safe='')}" if repo else "")
              + (f"&status={status}" if status != "all" else ""))
        here = f"<b>{sort.title()}</b>"
        there = f"<a href='/modules{qs}'>{other.title()}</a>"
        first, second = (here, there) if sort == "newest" else (there, here)
        parts.append(f"<p id='sort'><small>Sort: {first} · {second}</small></p>")
        parts.append(modfiltermod.tabbar(rows, status, sort, repo))
        keep_ids = {r["id"] for r in modfiltermod.filter_rows(rows, status)}
        shown = [e for e in enriched if e[0]["id"] in keep_ids]
        info = modpagesmod.paginate(shown, page)
        keep_params = {}
        if repo:
            keep_params["repo"] = repo
        if sort != "newest":
            keep_params["sort"] = sort
        if status != "all":
            keep_params["status"] = status
        parts.append("<div id='library'>")
        if not shown:
            parts.append("<p>No modules with this status yet.</p>")
        for mi, (m, stats, omap, order, owned_n, total, stale) in enumerate(info["items"]):
            n = stats["n"] or 0
            pct = int(round(100 * owned_n / total)) if total else 0
            chips = f"<span class='chip'>{n} concept{'s' if n != 1 else ''}</span>"
            if stale:
                chips += f" <span class='chip'>{stale} stale</span>"
            target = _first_unowned(omap, order)
            rid = " id='resume'" if mi == 0 else ""
            if target is not None:
                node = target.split(":", 1)[1] if ":" in target else target
                resume = (f"<p><a class='btn'{rid} "
                          f"href='/modules/{m['id']}#lesson-{lesmod.slug(node)}'>Resume</a></p>")
            else:
                resume = (f"<p><a class='btn'{rid} href='/modules/{m['id']}'>"
                          f"Review again</a></p>")
            inner = (f"<h3>{html.escape(m['task_summary'] or m['id'])}</h3>"
                     f"<small>{html.escape(m['created_at'] or '')}</small>"
                     f"<div class='bar' aria-hidden='true'><i style='width:{pct}%'></i></div>"
                     f"<p><small>{owned_n}/{total} concepts owned</small> {chips}</p>")
            parts.append(clickcardsmod.wrap_card(
                inner, f"/modules/{m['id']}",
                label=m["task_summary"] or m["id"]) + resume)
        parts.append(modpagesmod.summary_html(len(shown), info["page"]))
        parts.append(modpagesmod.pager_html(len(shown), info["page"],
                                            "/modules", keep_params))
        parts.append("<p id='exports'><small>Export: <a href='/export/anki.tsv'>Anki TSV</a> · "
                     "<a href='/feed.xml'>RSS feed</a></small></p>")
        parts.append("</div>")
        return "".join(parts)

    def module_html(self, mid: str, level: str = "auto") -> str:
        con = self._con()
        try:
            m = con.execute("SELECT * FROM modules WHERE id=?", (mid,)).fetchone()
            if m is None:
                return "<p>Unknown module.</p>"
            cards = con.execute(
                "SELECT cards.*, concepts.name AS concept FROM cards"
                " JOIN concepts ON concepts.id = cards.concept_id"
                " WHERE concepts.module_id=?", (mid,)).fetchall()
            concepts = con.execute(
                "SELECT id AS cid, name, kind, file, line, mastery FROM concepts"
                " WHERE module_id=?", (mid,)).fetchall()
            tries = quemod.attempts(con, [c["id"] for c in cards])
            history = quemod.history_by_card(con, mid)
            owned = ownmod.owned_map(con, mid)
            ladders = debtmod.bloom_reached(con, mid)
        finally:
            con.close()
        base = f"/modules/{mid}"
        try:
            lesson_map = {L["concept_id"]: L
                          for L in json.loads(m["lessons"] or "[]")}
        except (ValueError, KeyError):
            lesson_map = {}
        mastery_of = {}
        for row in concepts:
            node = row["cid"].split(":", 1)[1] if ":" in row["cid"] else row["cid"]
            mastery_of[node] = row["mastery"] or 0.0
        cards_by_concept: dict[str, list] = {}
        for c in cards:
            cards_by_concept.setdefault(c["concept_id"], []).append(c)
        parts = [crumbsmod.trail([("Modules", "/modules"),
                                         (m["task_summary"] or mid, None)]),
                   f"<p>{html.escape(m['task_summary'] or '')}</p>"]
        try:
            mission = m["purpose"]
        except (KeyError, IndexError):
            mission = ""
        if mission:
            parts.append(f"<p><b>Mission:</b> {html.escape(mission)}</p>")
        try:
            repo_line = f"{m['repo']} {m['commit_range']}".strip()
        except (KeyError, IndexError):
            repo_line = ""
        if repo_line:
            parts.append(f"<p><small>Session: {html.escape(repo_line)}</small></p>")
        parts.append(resetmod.reset_link_html(mid))
        parts.append(recentmod.record_js(mid, m["task_summary"] or mid))
        toc = []
        for row in concepts:
            node = row["cid"].split(":", 1)[1] if ":" in row["cid"] else row["cid"]
            mins = readtimemod.minutes_for(lesson_map.get(node, {}))
            toc.append(f"<a href='#lesson-{lesmod.slug(node)}'>{html.escape(row['name'])}</a> · {mins} min")
        if toc:
            parts.append(tochighlightmod.enhance_toc(
                f"<p class='toc' id='readtime'><small>In this module: {' · '.join(toc)}</small> <small>(minutes per lesson)</small></p>"))
        if concepts:
            owned_n = 0
            for row in concepts:
                cc = cards_by_concept.get(row["cid"], [])
                attempts, is_owned = owned.get(row["cid"], (0, False))
                if _concept_status(any(c["stale"] for c in cc),
                                   attempts, is_owned) == "Owned":
                    owned_n += 1
            pct = int(round(100 * owned_n / len(concepts)))
            parts.append(
                f"<div class='bar' role='img' aria-label='{owned_n} of "
                f"{len(concepts)} concepts owned'><i style='width:{pct}%'></i></div>"
                f"<p><small>{owned_n}/{len(concepts)} concepts owned</small></p>")
        practice_tagged = False
        dec_nodes = [r["cid"].split(":", 1)[1] if ":" in r["cid"] else r["cid"]
                     for r in concepts]
        dec_matches = decmod.matches_for_module(self.db_path, dec_nodes)
        cl_sums = claritymod.summaries(
            self.db_path, [r["cid"] for r in concepts])
        known_pending = knownmod.pending(
            self.db_path, [r["cid"] for r in concepts])
        for ci, row in enumerate(concepts):
            node = row["cid"].split(":", 1)[1] if ":" in row["cid"] else row["cid"]
            slug = lesmod.slug(node)
            concept_cards = cards_by_concept.get(row["cid"], [])
            concept_tries = sum(tries.get(c["id"], 0) for c in concept_cards)
            stale_any = any(c["stale"] for c in concept_cards)
            attempts, is_owned = owned.get(row["cid"], (concept_tries, False))
            status = _concept_status(stale_any, attempts, is_owned)
            stale = " <span class='stale'>[stale — code changed]</span>" if stale_any else ""
            ladder_extra = " id='ladder'" if ci == 0 else ""
            parts.append(
                f"<section id='lesson-{slug}'>"
                f"<h2>{html.escape(row['name'])}"
                f" {chiplinksmod.chip_link(mid, node, status)}"
                f"{debtmod.ladder_html(ladders.get(row['cid'], -1), ladder_extra)}{stale}</h2>"
                f"<p><small>{html.escape(row['kind'])} · "
                f"{html.escape(row['file'])}:{row['line']}</small></p>")
            if node in lesson_map:
                parts.append(lesmod.render_levels(
                    lesson_map[node], mastery_of[node], concept_tries,
                    level, base))
            parts.append(decmod.lesson_block(
                node, dec_matches.get(node, []), ci == 0))
            avg, nvotes = cl_sums.get(row["cid"], (0.0, 0))
            parts.append(claritymod.block_html(
                row["cid"], avg, nvotes, base, ci == 0))
            parts.append(knownmod.button_html(
                row["cid"], known_pending.get(row["cid"], ""), base,
                ci == 0))
            parts.append(reviewedmod.mark_control(row["cid"], ci == 0))
            if concept_cards:
                if not practice_tagged:
                    parts.append("<h3 id='practice'>Practice</h3>")
                    practice_tagged = True
                else:
                    parts.append("<h3>Practice</h3>")
            for c in concept_cards:
                lesson = (f"<details><summary>Study first — explained your way</summary>"
                          f"{lesmod.render_levels(lesson_map[node], mastery_of.get(node, 0.0), tries.get(c['id'], 0), level, base)}</details>"
                          if node in lesson_map else "")
                parts.append(
                    f"{cardlinksmod.article_open(c['id'])}<h3>{html.escape(c['concept'])} "
                    f"{cardsmod._difficulty_dots(c['difficulty'])}</h3>"
                    f"{lesson}"
                    f"{lesmod.why_html(c)}"
                    f"<p>{html.escape(c['front'])}</p>"
                    f"{cardsmod.answer_widget(c, tries.get(c['id'], 0), base)}"
                    f"{lesmod.submissions_html(history.get(c['id'], []))}</article>")
            parts.append(pagermod.pager_html(
                pagermod.section_slugs(concepts), ci, first=ci == 0))
            parts.append("</section>")
        parts.append(relmod.related_html(self.db_path, mid))
        parts.append("<a class='totop' href='#top'>Back to top ↑</a>")
        return "".join(parts)

    def journal_html(self) -> str:
        return journalmod.page_html(self.db_path)

    def tour_html(self) -> str:
        return tourmod.page_html(self.db_path)

    def status_html(self) -> str:
        return statusmod.page_html(self.db_path)

    # -- POST
    def do_POST(self):
        url = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode() if length else ""
        if url.path == "/mcp":
            try:
                msg = json.loads(raw)
                server = mcplib.MCPServer(self.db_path)
                result = server.dispatch(msg.get("method", ""), msg.get("params", {}))
                resp = {"jsonrpc": "2.0", "id": msg.get("id"), "result": result}
            except Exception as e:  # noqa: BLE001
                resp = {"jsonrpc": "2.0", "id": None, "error": {"message": str(e)}}
            data = json.dumps(resp).encode()
            self._send(data, 200, "application/json")
            return
        if url.path == "/journal":
            form = parse_qs(raw, keep_blank_values=True)
            out = journalmod.save(
                self.db_path, form.get("body", [""])[0])
            if "error" in out:
                body = (f"<p>Could not save: {html.escape(out['error'])}</p>"
                        f"<p><a class='btn' href='/journal'>Back</a></p>")
            else:
                body = (f"<p>Entry saved — private, always.</p>"
                        f"<p><a class='btn' href='/journal'>Back to Journal</a></p>")
            self._send(page("Journal", body, active="tour",
                            page_id="journal", counts=self._nav_counts()))
            return
        if url.path == "/diagnose":
            form = parse_qs(raw, keep_blank_values=True)
            trace = (form.get("trace", [""])[0] or "")[:20000]
            body = diamod.diagnose_html(self.db_path, trace)
            self._send(page("Diagnose", body, active="due", page_id="due",
                            lede="Paste a traceback — study first, then fix.",
                            counts=self._nav_counts()))
            return
        if url.path.startswith("/modules/") and url.path.endswith("/reset"):
            mid = url.path.split("/")[2]
            out = resetmod.reset_module(self.db_path, mid)
            if "error" in out:
                body = f"<p>Could not reset: {html.escape(out['error'])}</p>"
            else:
                body = (f"<p>Reset complete: {out['reviews_deleted']} "
                        f"review(s) deleted, {out['cards_reset']} card(s) "
                        f"back to fresh scheduling.</p>")
            body += (f"<p><a class='btn' href='/modules/{html.escape(mid)}'>"
                     f"Back to module</a></p>")
            self._send(page("Reset", body, active="modules",
                            page_id="modules", counts=self._nav_counts()))
            return
        if url.path.startswith("/concepts/") and url.path.endswith("/rate"):
            cid = url.path.split("/")[2]
            form = parse_qs(raw, keep_blank_values=True)
            origin = _safe_origin(form.get("origin", ["/modules"])[0])
            out = claritymod.record(
                self.db_path, cid, form.get("score", [""])[0])
            if "error" in out:
                body = (f"<p>Could not record: {html.escape(out['error'])}</p>"
                        f"<p><a class='btn' href='{html.escape(origin)}'>Back</a></p>")
            else:
                back = f"/modules/{out['module_id']}"
                body = (f"<p>Clarity vote recorded — thank you.</p>"
                        f"<p><a class='btn' href='{html.escape(back)}'>"
                        f"Back to module</a></p>")
            self._send(page("Clarity", body, counts=self._nav_counts()))
            return
        if url.path.startswith("/concepts/") and url.path.endswith("/known"):
            cid = url.path.split("/")[2]
            form = parse_qs(raw, keep_blank_values=True)
            origin = _safe_origin(form.get("origin", ["/modules"])[0])
            out = knownmod.skip(self.db_path, cid)
            if "error" in out:
                body = (f"<p>Could not skip: {html.escape(out['error'])}</p>"
                        f"<p><a class='btn' href='{html.escape(origin)}'>Back</a></p>")
            else:
                back = f"/modules/{out['module_id']}"
                body = (f"<p>Skipped — verification due "
                        f"<b>{html.escape(out['verify_due'][:10])}</b>.</p>"
                        f"<p><a class='btn' href='{html.escape(back)}'>"
                        f"Back to module</a></p>")
            self._send(page("Already know", body, counts=self._nav_counts()))
            return
        if url.path == "/reviews/undo":
            out = undomod.undo(self.db_path)
            if "error" in out:
                body = (f"<p>Could not undo: {html.escape(out['error'])}</p>"
                        f"<p><a class='btn' href='/reviews'>Back</a></p>")
            else:
                body = (f"<p>Undone review #{out['undone_review']} — "
                        f"scheduling restored.</p>"
                        f"<p><a class='btn' href='/reviews'>Back to History</a></p>")
            self._send(page("Undo", body, counts=self._nav_counts()))
            return
        if url.path.startswith("/cards/") and url.path.endswith("/snooze"):
            card_id = url.path.split("/")[2]
            form = parse_qs(raw, keep_blank_values=True)
            origin = _safe_origin(form.get("origin", ["/due"])[0])
            server = mcplib.MCPServer(self.db_path)
            out = server.snooze_card(card_id)
            if "error" in out:
                self._send(page("Error", "<p>Unknown card.</p>",
                                counts=self._nav_counts()), 404)
                return
            body = (f"<p>Snoozed until <b>{html.escape(out['due'])}</b> — "
                    f"no grade recorded.</p>"
                    f"<p><a class='btn' href='{html.escape(origin)}'>"
                    f"Back to queue</a></p>")
            self._send(page("Snoozed", body, counts=self._nav_counts()))
            return
        if url.path.startswith("/cards/") and url.path.endswith("/review"):
            card_id = url.path.split("/")[2]
            answer, conf_i, origin = _parse_review_form(raw)
            origin = scrollposmod.origin_with_anchor(origin, card_id)
            server = mcplib.MCPServer(self.db_path)
            out = server.submit_review(card_id, answer, conf_i)
            if "error" in out:
                self._send(page("Error", "<p>Unknown card.</p>",
                                counts=self._nav_counts()), 404)
                return
            res = out["result"]
            # Answer revealed only AFTER the attempt (principle 1).
            con = self._con()
            try:
                row = con.execute(
                    "SELECT cards.back, concepts.module_id FROM cards"
                    " JOIN concepts ON concepts.id = cards.concept_id"
                    " WHERE cards.id=?", (card_id,)).fetchone()
                back = row["back"]
                mod_id = row["module_id"]
            finally:
                con.close()
            due_left = server.tool_list_due_reviews({"limit": 1000})["count"]
            body = (scrollposmod.restore_js(origin)
                    + autoscrollmod.enhance_result(
                        resmod.render_result(res["pass"], res["feedback"], back,
                                             out["next_due"], origin, mod_id, due_left))
                    + autoscrollmod.verdict_js())
            self._send(page("Result", body, counts=self._nav_counts()))
            return
        if url.path.startswith("/cards/") and url.path.endswith("/dispute"):
            card_id = url.path.split("/")[2]
            form = parse_qs(raw, keep_blank_values=True)
            origin = _safe_origin(form.get("origin", ["/due"])[0])
            reason = (form.get("reason", [""])[0] or "")[:2000]
            out = dismod.open_dispute(self.db_path, card_id, reason)
            if "error" in out:
                body = (f"<p>Could not file: {html.escape(out['error'])}</p>"
                        f"<p><a class='btn' href='{html.escape(origin)}'>Back</a></p>")
            else:
                body = (f"<p>Dispute #{out['dispute_id']} filed — "
                        f"maintainers review it on the Status page.</p>"
                        f"<p><a class='btn' href='{html.escape(origin)}'>Back to queue</a></p>")
            self._send(page("Dispute", body, counts=self._nav_counts()))
            return
        if url.path.startswith("/disputes/") and url.path.endswith("/resolve"):
            try:
                did = int(url.path.split("/")[2])
            except ValueError:
                did = -1
            form = parse_qs(raw, keep_blank_values=True)
            verdict = (form.get("verdict", [""])[0] or "")
            out = dismod.resolve_dispute(self.db_path, did, verdict)
            if "error" in out:
                body = f"<p>Could not resolve: {html.escape(out['error'])}</p>"
            else:
                body = (f"<p>Dispute #{did} {html.escape(verdict)}.</p>")
            body += "<p><a class='btn' href='/status'>Back to Status</a></p>"
            self._send(page("Dispute", body, counts=self._nav_counts()))
            return
        self._send(page("Not found", errmod.not_found_html(url.path),
                        counts=self._nav_counts()), 404)


def serve(host: str = "127.0.0.1", port: int = 8765, db_path: str = "groundwork.db"):
    dbmod.init_db(db_path)
    Handler.db_path = db_path
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Groundwork UI at http://{host}:{port}/ (db: {db_path})")
    httpd.serve_forever()


def check_stale(db_path: str, repo: str) -> int:
    con = dbmod.connect(db_path)
    try:
        return modmod.mark_stale_cards(con, repo)
    finally:
        con.close()
