"""Web UI: stdlib HTTP server, server-rendered HTML, no build step.

Every screen asks for an answer before showing one (PRD principle 1).
Routes: / (due queue), /modules/<id> (practice), /reviews (FSRS queue),
POST /cards/<id>/review (grade), POST /mcp (HTTP JSON-RPC).
"""
from __future__ import annotations

import html
import json
import re
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

from . import api as apimod
from . import db as dbmod
from . import exercises as exmod
from . import exports as expmod
from . import mcp as mcplib
from . import modularity as modularitymod
from . import sitemap as sitemapmod
from . import modules as modmod
from . import sched as schedmod
from . import tour as tourmod

CSS = ("body{font-family:system-ui,-apple-system,sans-serif;max-width:48rem;"
       "margin:2rem auto;padding:0 1rem;line-height:1.55;color:#1a1a1a}"
       "nav{margin-bottom:1rem}nav a{margin-right:.25rem}"
       "h1{font-size:1.6rem}h2{font-size:1.25rem;margin-top:2rem;"
       "border-bottom:2px solid #1a1a1a;padding-bottom:.25rem}"
       "h3{font-size:1.05rem}h4{font-size:1rem;margin-bottom:.25rem}"
       "h5{font-size:.9rem;margin-bottom:.15rem;color:#333}"
       "article{border:1px solid #bbb;border-radius:10px;padding:1rem 1.25rem;"
       "margin:1rem 0;background:#fff}"
       "section{margin:1rem 0}"
       "pre{background:#f2f2f2;border:1px solid #ddd;border-radius:6px;"
       "padding:.6rem;overflow:auto;font-size:.85rem}"
       "blockquote{border-left:3px solid #666;margin:.5rem 0;padding:.25rem .75rem;"
       "color:#333;background:#fafafa}"
       "button{background:#1a1a1a;color:#fff;border:none;border-radius:6px;"
       "padding:.45rem .9rem;margin:.2rem;cursor:pointer;font-size:.9rem}"
       "button:hover{background:#333}"
       "input,select,textarea{border:1px solid #999;border-radius:6px;"
       "padding:.4rem;font-size:.9rem;margin:.15rem}"
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
       ".lede{color:#444;margin:.1rem 0 .5rem}"
       "nav a{padding:.2rem .5rem;border-radius:6px;text-decoration:none;color:#1a1a1a}"
       "nav a[aria-current=page]{background:#1a1a1a;color:#fff}"
       ".crumbs{font-size:.85rem;color:#555;margin:.5rem 0}"
       ".crumbs a{color:inherit}"
       "a.modcard{display:block;border:1px solid #bbb;border-radius:10px;"
       "padding:.75rem 1rem;margin:.75rem 0;text-decoration:none;color:inherit;background:#fff}"
       "a.modcard:hover{border-color:var(--accent,#1a1a1a)}"
       "a.modcard h3{margin:.1rem 0}"
       "a.modcard small{color:#555}"
       ".chip{display:inline-block;font-size:.75rem;border:1px solid #999;"
       "border-radius:999px;padding:.05rem .5rem;margin-right:.25rem;color:#333}"
       ".bar{height:.5rem;background:#e6e6e6;border-radius:4px;overflow:hidden;margin:.4rem 0}"
       ".bar i{display:block;height:100%;background:var(--accent,#1a1a1a)}"
       "table.log{width:100%}"
       "footer.page-foot{margin-top:2rem;padding-top:.75rem;border-top:1px solid #ddd;"
       "font-size:.85rem;color:#555}"
       "html{scroll-behavior:smooth}"
       "@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}"
       "article.next{border:2px solid var(--accent,#1a1a1a)}"
       ".next-tag{font-weight:700;color:var(--accent,#1a1a1a);margin:.2rem 0}"
       "p.toc{position:sticky;top:0;background:#fff;padding:.4rem 0;"
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
       "button.giveup{background:none;color:#666;text-decoration:underline;"
       "padding:.2rem;font-size:.85rem}"
       "button.giveup:hover{background:none;color:#1a1a1a}"
       ".ladder{display:inline-flex;align-items:flex-end;gap:2px;margin-left:.4rem}"
       ".ladder i{width:8px;background:#ddd;border-radius:2px}"
       ".ladder i.on{background:var(--accent,#1a1a1a)}"
       ".copybtn{position:absolute;top:.3rem;right:.3rem;font-size:.75rem;"
       "padding:.2rem .5rem}"
       "a{color:var(--accent,#1a1a1a)}"
       "a:visited{color:var(--accent,#1a1a1a)}"
       "nav a:visited{color:#1a1a1a}"
       "nav a[aria-current=page]:visited{color:#fff}"
       "a.btn{display:inline-block;background:#1a1a1a;color:#fff;"
       "border-radius:6px;padding:.45rem .9rem;margin:.2rem;"
       "text-decoration:none;font-size:.9rem}"
       "a.btn:hover{background:#333}"
       "a.btn:visited{color:#fff}"
       ":target{outline:3px solid var(--accent,#1a1a1a);outline-offset:3px}"
       ".tour-banner{border:2px solid var(--accent,#1a1a1a);border-radius:10px;"
       "padding:.6rem .9rem;margin:0 0 1rem;background:#fff}"
       ".tour-banner small{color:#555}"
       ".tour-steps{list-style:none;padding-left:0}"
       ".tour-steps li{margin:.6rem 0}"
       ".status-ok{color:#0a0;font-weight:700}"
       ".status-missing{color:#a00;font-weight:700}"
       "a.totop{position:fixed;bottom:1rem;right:1rem;background:#1a1a1a;"
       "color:#fff;border-radius:999px;padding:.5rem .9rem;font-size:.85rem;"
       "text-decoration:none}"
       "a.totop:visited{color:#fff}"
       "a.totop:hover{background:#333}")


def _payload(card) -> dict:
    raw = card.get("payload", "{}") if isinstance(card, dict) else card["payload"]
    try:
        return json.loads(raw or "{}")
    except ValueError:
        return {}


def _confidence(extra: str = "") -> str:
    pills = "".join(
        f"<label class='conf'><input type='radio' name='confidence' "
        f"value='{i}'{' checked' if i == 3 else ''}>{i}</label>"
        for i in (1, 2, 3, 4, 5))
    return f"<span class='conf-group'{extra}>Confidence {pills}</span> "


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


PARSONS_JS = """
<script>
if (!window.__parsonsInit) { window.__parsonsInit = true;
function parsonsSync(ol) {
  var ids = Array.prototype.map.call(
    ol.querySelectorAll('li'), function (li) { return li.getAttribute('data-i'); });
  document.getElementById('po-' + ol.id.slice(3)).value = ids.join(' ');
}
document.addEventListener('DOMContentLoaded', function () {
  Array.prototype.forEach.call(document.querySelectorAll('ol.parsons'), function (ol) {
    var dragged = null;
    parsonsSync(ol);
    ol.addEventListener('dragstart', function (e) {
      dragged = e.target.closest('li'); e.dataTransfer.effectAllowed = 'move';
    });
    ol.addEventListener('dragover', function (e) {
      e.preventDefault();
      var li = e.target.closest('li');
      if (li && li !== dragged) {
        var r = li.getBoundingClientRect();
        var after = (e.clientY - r.top) > r.height / 2;
        ol.insertBefore(dragged, after ? li.nextSibling : li);
      }
    });
    ol.addEventListener('drop', function (e) { e.preventDefault(); parsonsSync(ol); });
    ol.addEventListener('click', function (e) {
      var b = e.target.closest('button[data-move]'); if (!b) return;
      var li = b.closest('li'); var d = parseInt(b.getAttribute('data-move'), 10);
      if (d < 0 && li.previousElementSibling) ol.insertBefore(li, li.previousElementSibling);
      if (d > 0 && li.nextElementSibling) ol.insertBefore(li.nextElementSibling, li);
      parsonsSync(ol);
    });
  });
});
}
</script>"""


def render_levels(lesson: dict, mastery: float, attempts: int,
                    level_override: str, base_path: str) -> str:
    """Leveled explainer with tabs; auto-places from mastery by default."""
    from . import explain as explainmod
    levels = explainmod.levels_for(lesson)
    if level_override in ("1", "2", "3", "4"):
        active = int(level_override)
    else:
        active = explainmod.auto_level(mastery or 0.0, attempts)
    tabs = []
    for n in ("auto", "1", "2", "3", "4"):
        label = "Auto" if n == "auto" else explainmod.LEVEL_TITLES[int(n)]
        mark = " <b>(you are here)</b>" if (
            (n == "auto" and level_override not in ("1", "2", "3", "4")) or
            (n != "auto" and int(n) == active and
             level_override in ("1", "2", "3", "4"))) else ""
        tabs.append(f"<a href='{base_path}?level={n}'>{label}</a>{mark}")
    out = [f"<p><small>Explain it {'simply' if active <= 2 else 'technically'}: "
           f"{' · '.join(tabs)}</small></p>"]
    lv = next(L for L in levels if L["n"] == active)
    out.append(f"<h4>{html.escape(lv['title'])}</h4>")
    for blk in lv["blocks"]:
        body = html.escape(blk["b"])
        if blk.get("pre"):
            out.append(f"<h5>{html.escape(blk['h'])}</h5><pre>{body}</pre>")
        else:
            out.append(f"<h5>{html.escape(blk['h'])}</h5>"
                       f"<p>{body.replace(chr(10), '<br>')}</p>")
    if lv.get("code") and not any(b.get("pre") for b in lv["blocks"]):
        out.append(f"<details><summary>Show me the code</summary>"
                   f"<pre>{html.escape(lv['code'])}</pre></details>")
    return "".join(out)


def why_html(card) -> str:
    from . import pipeline as pipelinemod
    why = _payload(card).get("why", "")
    if not why:
        return ""
    if why == pipelinemod.UNSTATED_WHY:
        return (f"<p class='unstated'><small><b>Why this matters:</b> "
                f"{html.escape(why)}</small></p>")
    return f"<p><small><b>Why this matters:</b> {html.escape(why)}</small></p>"


def hints_html(card, attempts: int = 0) -> str:
    """Progressive hint reveal (adaptive scaffolding): the nudge is always
    visible; each further attempt unlocks the next tier."""
    hints = _payload(card).get("hints", [])
    shown = hints[:min(len(hints), 1 + attempts)]
    if not shown:
        return ""
    return "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(shown))


def answer_widget(card, attempts: int = 0, origin: str = "/") -> str:
    """Interaction matched to the exercise type — never just answer+submit.

    `origin` records the page the card was answered from so the result
    screen can link back to it (navigation contract: never strand).
    """
    cid = card["id"]
    etype = str(card["exercise_type"] if isinstance(card, dict)
                else card["exercise_type"])
    p = _payload(card)
    open_form = (f"<form method='post' action='/cards/{cid}/review'>"
                 f"<input type='hidden' name='origin' value='{html.escape(origin, quote=True)}'>")
    if etype == "1":
        opts = "".join(f"<option value='{i}'>{i} — {w}</option>"
                       for i, w in enumerate(
                           ["blank", "wrong", "shaky", "close", "right", "easy"]))
        body = (f"<label>Say it back in your own words first "
                f"(optional, this is the recall):<br>"
                f"<textarea name='recall' rows='3' cols='60'></textarea></label><br>"
                f"<label>Then rate how well you recalled it: "
                f"<select name='answer'>{opts}</select></label> "
                f"{_confidence()}<button>Submit rating</button>")
    elif etype == "2":
        blanks = p.get("blanks") or [{"id": 0, "answers": p.get("answers", [])}]
        fields = " ".join(
            f"<label>___({b['id']}) <input name='b{b['id']}' size='12'></label>"
            for b in blanks)
        body = f"{fields} {_confidence()}<button>Check blanks</button>"
    elif etype in ("4", "7", "16", "18"):
        btns = " ".join(
            f"<button name='answer' value='{html.escape(c)}'>{html.escape(c)}</button>"
            for c in p.get("choices", []))
        body = f"{btns} {_confidence()}"
    elif etype in ("5", "6", "21", "22", "24", "25"):
        hint = ("First line: A or B, then your reasons."
                if etype == "22" else "Explain in your own words…")
        body = (f"<textarea name='answer' rows='5' cols='70' "
                f"placeholder='{hint}'></textarea><br>"
                f"{_confidence()}<button>Submit explanation</button>")
    elif etype == "8":
        if p.get("choices"):
            btns = " ".join(
                f"<button name='answer' value='{html.escape(c)}'>{html.escape(c)}</button>"
                for c in p["choices"])
            body = (f"<p>Pick the output — or type it from memory when these feel easy:</p>"
                    f"{btns}<br>"
                    f"<label>Type it: <input name='answer' size='20'></label> "
                    f"{_confidence()}<button>Check</button>")
        else:
            body = (f"<label>It prints/returns: <input name='answer' size='30'></label> "
                    f"{_confidence()}<button>Check prediction</button>")
    elif etype == "3" and p.get("choices"):
        btns = " ".join(
            f"<button name='answer' value='{html.escape(c)}'>{html.escape(c)}</button>"
            for c in p["choices"])
        body = (f"<p>Pick the signature — or write it from memory when these feel easy:</p>"
                f"{btns}<br>"
                f"<label>Write it: <input name='answer' size='40'></label> "
                f"{_confidence()}<button>Check</button>")
    elif etype == "30":
        left = p.get("left", [])
        right = p.get("right", [])
        letters = " ".join(f"<b>{chr(ord('A') + i)}</b> {html.escape(b)}"
                           for i, b in enumerate(right))
        rows = "".join(
            f"<tr><td><b>{i}</b> {html.escape(a)}</td>"
            f"<td><input name='m{i}' size='3' placeholder='letter'></td></tr>"
            for i, a in enumerate(left))
        body = (f"<p>{letters}</p><table>{rows}</table>"
                f"{_confidence()}<button>Check matches</button>")
    elif etype == "9":
        steps = p.get("expected", [])
        rows = "".join(
            f"<tr><td>Step {i + 1}</td>"
            f"<td><input name='s{i}' size='12'></td></tr>"
            for i in range(len(steps))) or \
            "<tr><td>Value</td><td><input name='s0' size='12'></td></tr>"
        body = (f"<table>{rows}</table>{_confidence()}"
                f"<button>Check trace</button>")
    elif etype in ("10", "11"):
        items = "".join(
            f"<li draggable='true' data-i='{i}'>"
            f"<span class='grip'>⠿</span> {html.escape(l)} "
            f"<button type='button' data-move='-1'>↑</button>"
            f"<button type='button' data-move='1'>↓</button></li>"
            for i, l in enumerate(p.get("lines", [])))
        body = (f"<p>Drag the lines into order (or type the numbers):</p>"
                f"<ol class='parsons' id='pl-{cid}'>{items}</ol>"
                f"<input type='hidden' name='answer' id='po-{cid}' value=''>"
                f"<label>Order (numbers): "
                f"<input name='answer_text' size='30' placeholder='0 1 2 …'></label> "
                f"{_confidence()}<button>Check order</button>{PARSONS_JS}")
    elif etype in ("12", "14", "19", "20", "23"):
        body = (f"<textarea name='answer' rows='12' cols='70' "
                f"placeholder='Write your code here'></textarea><br>"
                f"{_confidence()}<button>Run tests</button>")
    elif etype == "13":
        opts = "".join(
            f"<label><input type='radio' name='answer' value='{i + 1}'> "
            f"{html.escape(l)}</label><br>"
            for i, l in enumerate(p.get("snippet", "").splitlines()))
        body = f"{opts}{_confidence()}<button>Accuse this line</button>"
    else:
        body = (f"<input name='answer' size='50' placeholder='Your answer'> "
                f"{_confidence()}<button>Submit</button>")
    giveup = (f"<form method='post' action='/cards/{cid}/review'>"
              f"<input type='hidden' name='answer' value=''>"
              f"<input type='hidden' name='confidence' value='1'>"
              f"<input type='hidden' name='origin' value='{html.escape(origin, quote=True)}'>"
              f"<button class='giveup'>Give up — show me the answer</button></form>")
    return f"{open_form}{body}</form>" + hints_html(card, attempts) + giveup


NAV = (("projects", "/", "Projects"),
       ("due", "/due", "Due"),
       ("modules", "/modules", "Modules"),
       ("history", "/reviews", "History"),
       ("debt", "/debt", "Debt"),
       ("tour", "/tour", "Tour"))


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
    def _label(key: str, label: str) -> str:
        if counts and counts.get(key) is not None:
            return f"{label} ({counts[key]})"
        return label
    links = " · ".join(
        f"<a href='{href}'{(' aria-current=\"page\"' if key == active else '')}>"
        f"{_label(key, label)}</a>"
        for key, href, label in NAV)
    head = (f"<header class='page-head' id='top'><nav id='sitenav'>{links}</nav>"
            f"<h1>{html.escape(title)}</h1>")
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
    foot = ("<footer class='page-foot'>Groundwork — every session leaves you smarter.<br>"
            "<a href='/'>Projects</a> · <a href='/due'>Due</a> · "
            "<a href='/modules'>Modules</a> · <a href='/reviews'>History</a> · "
            "<a href='/debt'>Debt</a> · <a href='/tour'>Tour</a> · "
            "<a href='/status'>Status</a></footer>")
    body = banner + body
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
            f"<body data-page='{page_id}'>{head}{body}{foot}{GLOBAL_JS}"
            f"</body></html>").encode()


def _slug(text: str) -> str:
    """URL-fragment-safe anchor slug for a lesson section."""
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    out = "-".join(filter(None, out.split("-")))
    return out or "lesson"


def _ownership_types() -> list[str]:
    """Exercise types that prove modification skill (modify/create Bloom)."""
    return [str(t) for bloom in ("modify", "create")
            for t in exmod.BLOOM_TYPES.get(bloom, [])]


def _owned_map(con, mid: str) -> dict:
    """Per-concept (attempts, owned) for one module.

    Owned follows the PRD mastery model: a spaced modify/create pass —
    a passing grade on a modify/create card plus a return visit
    (2+ attempts), so same-day fluency alone never counts as owned.
    """
    types = _ownership_types()
    q = ("SELECT concepts.id AS cid, COUNT(reviews.id) AS attempts,"
         " SUM(CASE WHEN reviews.grade >= 4" +
         (f" AND cards.exercise_type IN ({','.join('?' * len(types))})"
          if types else " AND 0") +
         " THEN 1 ELSE 0 END) AS own_pass"
         " FROM concepts LEFT JOIN cards ON cards.concept_id = concepts.id"
         " LEFT JOIN reviews ON reviews.card_id = cards.id"
         " WHERE concepts.module_id=? GROUP BY concepts.id")
    args = list(types) + [mid] if types else [mid]
    out = {}
    for r in con.execute(q, args).fetchall():
        attempts = r["attempts"] or 0
        out[r["cid"]] = (attempts, bool(r["own_pass"]) and attempts >= 2)
    return out


def _due_why(card, extra: str = "") -> str:
    """Scheduler explainability: why is this card due today?"""
    get = card.get if isinstance(card, dict) else lambda k: card[k]
    try:
        from . import sched as schedmod
        due = schedmod.parse_iso(str(get("due") or ""))
        days = (schedmod.utcnow() - due).days
        when = "due today" if days <= 0 else f"{days}d overdue"
    except Exception:  # noqa: BLE001 — bad date still renders
        when = "due now"
    try:
        stab = float(get("stability") or 0.0)
    except (TypeError, ValueError):
        stab = 0.0
    lapses = get("lapses") or 0
    tip = (f"{when}; memory strength {stab:.1f} days; "
           f"lapses {lapses}")
    return (f" <small><span{extra} title='{html.escape(tip)}'>"
            f"why due?</span></small>")


_WEEK_SECS = 7 * 86400


def _rel_time(iso_ts: str) -> str:
    """Relative time with exact timestamp on hover (I-25, I-26, I-93).

    Renders `<time datetime>` so dates read as "3h ago" but keep their
    exact, timezone-explicit value one hover away.
    """
    raw = iso_ts or ""
    try:
        from . import sched as schedmod
        stamp = schedmod.parse_iso(raw)
        delta = schedmod.utcnow() - stamp
        secs = int(delta.total_seconds())
        if secs < 0:
            rel = "in the future"
        elif secs < 90:
            rel = "just now"
        elif secs < 5400:
            rel = f"{secs // 60}m ago"
        elif secs < 129600:
            rel = f"{secs // 3600}h ago"
        elif secs < _WEEK_SECS:
            rel = f"{secs // 86400}d ago"
        else:
            rel = raw[:10]
    except Exception:  # noqa: BLE001 — bad date still renders
        rel = raw[:10] or "unknown"
    return (f"<time datetime='{html.escape(raw)}' title='{html.escape(raw)}'>"
            f"{html.escape(rel)}</time>")


def _memory_bar(card, extra: str = "") -> str:
    """Memory-strength bar from the FSRS stability estimate (I-76)."""
    get = card.get if isinstance(card, dict) else lambda k: card[k]
    try:
        stab = float(get("stability") or 0.0)
    except (TypeError, ValueError):
        return ""
    try:
        retr = float(get("retrievability") or 0.0)
    except (TypeError, ValueError):
        retr = 0.0
    pct = int(round(max(0.0, min(1.0, retr if retr > 0 else stab / 30.0)) * 100))
    return (f"<p{extra}><small>Memory strength {stab:.1f}d</small>"
            f"<span class='bar' aria-hidden='true'>"
            f"<i style='width:{pct}%'></i></span></p>")


def _difficulty_dots(difficulty, extra: str = "") -> str:
    """5-dot difficulty meter from the FSRS difficulty estimate."""
    try:
        n = int(round(float(difficulty if difficulty is not None else 0.5) * 5))
    except (TypeError, ValueError):
        n = 3
    n = max(1, min(5, n))
    return (f"<small{extra} title='Difficulty {n}/5'>"
            f"{'●' * n}{'○' * (5 - n)}</small>")


BLOOM_RUNGS = ["recall", "explain", "apply", "analyse", "modify", "create"]


def _bloom_reached(con, mid: str) -> dict:
    """Highest Bloom rung with a passing review, per concept in a module."""
    rung_of = {}
    for t, (_name, bloom) in exmod.TYPES.items():
        rung_of[str(t)] = BLOOM_RUNGS.index(bloom) if bloom in BLOOM_RUNGS else -1
    out: dict[str, int] = {}
    try:
        rows = con.execute(
            "SELECT cards.concept_id, cards.exercise_type FROM reviews"
            " JOIN cards ON cards.id = reviews.card_id"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=? AND reviews.grade >= 4",
            (mid,)).fetchall()
    except Exception:  # noqa: BLE001 — no reviews yet still renders
        return out
    for r in rows:
        rung = rung_of.get(str(r["exercise_type"]), -1)
        if rung >= 0:
            out[r["concept_id"]] = max(out.get(r["concept_id"], -1), rung)
    return out


def _ladder_html(reached: int, extra: str = "") -> str:
    """Six ascending rungs; lit rungs mark demonstrated skill tiers."""
    bars = []
    for i, bloom in enumerate(BLOOM_RUNGS):
        cls = "on" if i <= reached else "off"
        bars.append(f"<i class='{cls}' style='height:{4 + 2 * i}px' "
                    f"title='{bloom}'></i>")
    return (f"<span class='ladder'{extra} title='Highest demonstrated: "
            f"{BLOOM_RUNGS[reached] if reached >= 0 else 'none yet'}'>"
            + "".join(bars) + "</span>")


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


COACH_TIPS = {
    "recall": "Say the answer aloud before rating yourself.",
    "explain": "Check your explanation against the study guide sentence by sentence.",
    "apply": "Predict the outcome before you run anything or peek.",
    "analyse": "Point at the exact line before committing to an answer.",
    "modify": "Run the mental test suite before submitting.",
    "evaluate": "Name the flaw precisely before judging.",
    "create": "Compare your version against the spec line by line.",
    "other": "Slow down on the hard ones.",
}


def calibration_coach(rows: list) -> str:
    """Per-skill accuracy-vs-confidence table plus an overconfidence nudge.

    rows: (exercise_type, grade 0-5, confidence 1-5). A skill earns a
    coaching nudge with 3+ attempts and confidence beating accuracy
    by 15+ points — the blind spot in AI-assisted work.
    """
    by_bloom: dict[str, list] = {}
    for etype, grade, conf in rows:
        try:
            bloom = exmod.TYPES[int(etype)][1]
        except (ValueError, KeyError, TypeError):
            bloom = "other"
        by_bloom.setdefault(bloom, []).append((grade, conf))
    if not by_bloom:
        return ""
    cells = []
    worst = None
    for bloom in sorted(by_bloom):
        rs = by_bloom[bloom]
        acc = sum(1 for g, _ in rs if (g or 0) >= 4) / len(rs)
        avg_conf = sum(((c or 3) - 1) / 4 for _, c in rs) / len(rs)
        gap = avg_conf - acc
        cells.append(f"<tr><td>{html.escape(bloom)}</td><td>{acc:.0%}</td>"
                     f"<td>{avg_conf:.0%}</td><td>{gap:+.0%}</td></tr>")
        if len(rs) >= 3 and gap >= 0.15 and (worst is None or gap > worst[1]):
            worst = (bloom, gap, acc, avg_conf)
    parts = ["<h2>Calibration coach</h2>",
             "<table class='log'><tr><th>Skill</th><th>Accuracy</th>"
             "<th>Confidence</th><th>Gap</th></tr>" + "".join(cells) + "</table>"]
    if worst is not None:
        bloom, _, acc, avg_conf = worst
        parts.append(f"<p>Coach: on {html.escape(bloom)} exercises you feel "
                     f"{avg_conf:.0%} confident but score {acc:.0%}. "
                     f"{COACH_TIPS.get(bloom, COACH_TIPS['other'])}</p>")
    return "".join(parts)


def _trace_symbols(text: str) -> list[str]:
    """Symbol names mentioned in a pasted Python traceback, most recent last."""
    frames = re.findall(r'File "[^"]+", line \d+, in (\S+)', text)
    names = re.findall(r"(?:NameError|AttributeError)[^:\n]*:?[^'\"]*['\"]([\w_]+)['\"]", text)
    seen = []
    for n in frames + names:
        if n != "<module>" and n not in seen:
            seen.append(n)
    return seen


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


def result_nav(origin: str, mod_id: str) -> str:
    """Never strand: back to origin, module, queue and history."""
    back_link = f"/modules/{mod_id}" if mod_id else "/"
    links = (f"<p><a class='btn' href='{html.escape(origin)}'>"
             f"Continue where you left off</a>")
    if back_link != origin:
        links += f" · <a href='{back_link}'>Back to module</a>"
    links += " · <a href='/due'>Due queue</a> · <a href='/reviews'>History</a></p>"
    return links


def render_result(passed: bool, feedback: str, back: str, next_due: str,
                  origin: str, mod_id: str, due_left: int | None = None) -> str:
    """Result screen: verdict first, explanation, then where to go next."""
    cls = "ok" if passed else "stale"
    verdict = "✓ Correct" if passed else "✗ Not yet"
    left = (f"<p><small>{due_left} more card{'s' if due_left != 1 else ''} "
            f"due.</small></p>" if due_left else "")
    return (f"<p class='verdict {cls}'>{verdict} — {html.escape(feedback)}</p>"
            f"<details open><summary>Explanation</summary><p>{html.escape(back)}</p></details>"
            f"<p>Next review: {html.escape(next_due)}</p>"
            f"{left}{result_nav(origin, mod_id)}")


class Handler(BaseHTTPRequestHandler):
    db_path = "groundwork.db"

    def log_message(self, *a):
        pass

    # -- helpers
    def _send(self, data: bytes, code: int = 200, ctype: str = "text/html"):
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
        level = query.get("level", ["auto"])[0]
        counts = self._nav_counts()
        tour_ctx = None
        tour_id = query.get("tour", [""])[0]
        if tour_id in tourmod.BY_ID:
            mid, lesson = self._tour_targets()
            tour_ctx = tourmod.context(tour_id, mid, lesson)
        if url.path == "/":
            self._send(page("Projects", self.projects_html(),
                            active="projects", page_id="projects",
                            lede="Every repo you are learning — pick one and study it.",
                            counts=counts, tour=tour_ctx))
        elif url.path == "/due":
            self._send(page("Due", self.due_html(level),
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
            lede = (f"Modules in {repo} — pick one and study it." if repo
                    else "Every agent session as a lesson — pick one and study it.")
            self._send(page("Modules", self.modules_html(repo, sort),
                            active="modules", page_id="modules",
                            lede=lede, counts=counts, tour=tour_ctx))
        elif url.path == "/debt":
            self._send(page("Debt", self.debt_html(),
                            active="debt", page_id="debt",
                            lede="What changed versus what you can prove — pay it down.",
                            counts=counts, tour=tour_ctx))
        elif url.path == "/diagnose":
            self._send(page("Diagnose", self.diagnose_html(),
                            active="due", page_id="due",
                            lede="Paste a traceback — study first, then fix.",
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
        elif url.path == "/export/anki.tsv":
            self._send(self.anki_tsv().encode(), 200,
                       "text/tab-separated-values; charset=utf-8")
        elif url.path == "/export/reviews.csv":
            self._send(self.reviews_csv().encode(), 200,
                       "text/csv; charset=utf-8")
        elif url.path == "/api/modules.json":
            self._send(self.api_modules().encode(), 200,
                       "application/json; charset=utf-8")
        elif url.path == "/api/due.json":
            self._send(self.api_due().encode(), 200,
                       "application/json; charset=utf-8")
        elif url.path == "/feed.xml":
            host = self.headers.get("Host", "127.0.0.1:8765")
            self._send(self.feed_xml(f"http://{host}").encode(), 200,
                       "application/rss+xml; charset=utf-8")
        elif url.path == "/sitemap.xml":
            host = self.headers.get("Host", "127.0.0.1:8765")
            self._send(self.sitemap_xml(f"http://{host}").encode(), 200,
                       "application/xml; charset=utf-8")
        elif url.path == "/robots.txt":
            host = self.headers.get("Host", "127.0.0.1:8765")
            self._send(self.robots_txt(f"http://{host}").encode(), 200,
                       "text/plain; charset=utf-8")
        elif url.path.startswith("/modules/"):
            mid = url.path.split("/")[-1]
            body = self.module_html(mid, level)
            if body == "<p>Unknown module.</p>":
                self._send(page("Not found", body, active="modules",
                                page_id="modules", counts=counts,
                                tour=tour_ctx), 404)
            else:
                self._send(page("Module", body, active="modules",
                                page_id="modules", counts=counts,
                                tour=tour_ctx))
        else:
            self._send(b"not found", 404, "text/plain")

    def due_html(self, level: str = "auto") -> str:
        server = mcplib.MCPServer(self.db_path)
        due = server.tool_list_due_reviews({"limit": 20})["due"]
        parts = []
        if not due:
            parts.append("<p>Nothing due. Create a module via the MCP tool, "
                         "or browse <a href='/modules'>Modules</a>.</p>")
        con2 = self._con()
        try:
            study = self._stored_lessons(con2, [c["id"] for c in due])
            tries = self._attempts(con2, [c["id"] for c in due])
        finally:
            con2.close()
        for i, c in enumerate(due):
            stale = " <span class='stale'>[stale]</span>" if c.get("stale") else ""
            if c["id"] in study:
                lesson_dict, mastery = study[c["id"]]
                explainer = render_levels(
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
            dots = _difficulty_dots(
                c.get("difficulty"), " id='difficulty'" if first else "")
            widget = answer_widget(c, tries.get(c["id"], 0), "/due")
            why_extra = ""
            if first:
                # Stable tour anchors on the lead card only.
                why_extra = " id='due-why'"
                widget = widget.replace(
                    "<span class='conf-group'>",
                    "<span class='conf-group' id='confidence'>", 1)
                widget = widget.replace(
                    "<button class='giveup'>",
                    "<button class='giveup' id='giveup'>", 1)
            mem = _memory_bar(
                c, " id='memory'" if first else "")
            snooze_id = " id='snooze'" if first else ""
            snooze = (
                f"<form method='post' action='/cards/{c['id']}/snooze'>"
                f"<input type='hidden' name='origin' value='/due'>"
                f"<button{snooze_id}>Snooze until tomorrow</button></form>")
            parts.append(
                f"<article{cls}>{tag}{pos}{_due_why(c, why_extra)}"
                f"<h3>{html.escape(c.get('concept', ''))}{stale} {dots}</h3>"
                f"{mem}{lesson}"
                f"{why_html(c)}"
                f"<p>{html.escape(c.get('front', ''))}</p>"
                f"{widget}{snooze}</article>")
        parts.append("<p><a class='btn' href='/modules'>Browse all modules</a> "
                     "<a class='btn' href='/reviews'>Review history</a> "
                     "<a class='btn' href='/diagnose'>Diagnose a traceback</a></p>")
        return "<div id='queue'>" + "".join(parts) + "</div>"

    def history_html(self) -> str:
        """Past attempts: grades, confidence, calibration — not a second queue."""
        con = self._con()
        try:
            cal = con.execute(
                "SELECT AVG(grade) AS g, AVG(confidence) AS c, COUNT(*) AS n FROM reviews"
            ).fetchone()
            days = con.execute(
                "SELECT substr(reviewed_at, 1, 10) AS d, COUNT(*) AS n,"
                " SUM(CASE WHEN grade >= 4 THEN 1 ELSE 0 END) AS ok"
                " FROM reviews GROUP BY d ORDER BY d DESC LIMIT 14").fetchall()
            week = con.execute(
                "SELECT COUNT(*) AS n,"
                " SUM(CASE WHEN grade >= 4 THEN 1 ELSE 0 END) AS ok,"
                " COUNT(DISTINCT substr(reviewed_at, 1, 10)) AS days"
                " FROM reviews WHERE reviewed_at >= ?",
                ((schedmod.utcnow() - timedelta(days=7)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"),)).fetchone()
            rows = con.execute(
                "SELECT reviews.grade, reviews.confidence, reviews.reviewed_at,"
                " concepts.name AS concept, concepts.module_id AS module_id,"
                " modules.task_summary AS summary"
                " FROM reviews JOIN cards ON cards.id = reviews.card_id"
                " JOIN concepts ON concepts.id = cards.concept_id"
                " JOIN modules ON modules.id = concepts.module_id"
                " ORDER BY reviews.id DESC LIMIT 100").fetchall()
            coach_rows = con.execute(
                "SELECT cards.exercise_type, reviews.grade, reviews.confidence"
                " FROM reviews JOIN cards ON cards.id = reviews.card_id"
                " ORDER BY reviews.id DESC LIMIT 500").fetchall()
            tl_mods = [dict(r) for r in con.execute(
                "SELECT id, task_summary, created_at, repo FROM modules"
                " ORDER BY created_at DESC LIMIT 30").fetchall()]
            tl_stats = {}
            for tm in tl_mods:
                omap = _owned_map(con, tm["id"])
                cards_n = con.execute(
                    "SELECT COUNT(*) FROM cards JOIN concepts"
                    " ON concepts.id = cards.concept_id"
                    " WHERE concepts.module_id=?",
                    (tm["id"],)).fetchone()[0]
                tries_n = con.execute(
                    "SELECT COUNT(*) FROM reviews JOIN cards"
                    " ON cards.id = reviews.card_id JOIN concepts"
                    " ON concepts.id = cards.concept_id"
                    " WHERE concepts.module_id=?",
                    (tm["id"],)).fetchone()[0]
                tl_stats[tm["id"]] = (cards_n, tries_n, omap)
        finally:
            con.close()
        parts = []
        if cal and cal["n"]:
            acc = (cal["g"] or 0) / 5.0
            conf = ((cal["c"] or 3) - 1) / 4.0
            parts.append(f"<p id='calibration'>Calibration: accuracy {acc:.0%} vs confidence {conf:.0%} "
                         f"(gap {conf - acc:+.0%}, n={cal['n']})</p>")
            parts.append(calibration_coach(
                [(r[0], r[1], r[2]) for r in coach_rows]))
            if tl_mods:
                tl_rows = []
                for tm in tl_mods:
                    cards_n, tries_n, omap = tl_stats[tm["id"]]
                    owned_n = sum(1 for _, o in omap.values() if o)
                    date = (tm["created_at"] or "")[:10]
                    tl_rows.append(
                        f"<tr><td>{html.escape(date)}</td>"
                        f"<td><a href='/modules/{tm['id']}'>"
                        f"{html.escape(tm['task_summary'] or tm['id'])}</a>"
                        f"<br><small>{html.escape(tm['repo'] or '')}</small></td>"
                        f"<td>{cards_n}</td><td>{tries_n}</td>"
                        f"<td>{owned_n}/{len(omap)}</td></tr>")
                parts.append("<h2 id='coverage'>Coverage timeline</h2>"
                             "<p><small>Every session, what it made, "
                             "and what stuck.</small></p>"
                             "<table class='log'><tr><th>Date</th><th>Session</th>"
                             "<th>Cards</th><th>Attempts</th><th>Owned</th></tr>"
                             + "".join(tl_rows) + "</table>")
        else:
            parts.append("<p>No attempts yet. Answer a card on the "
                         "<a href='/due'>Due</a> page and it will show up here.</p>")
            return "".join(parts)
        if days:
            cells = "".join(
                f"<tr><td>{html.escape(d['d'])}</td><td>{d['n']}</td>"
                f"<td>{d['ok']}</td></tr>" for d in days)
            parts.append("<h2>Last 14 practice days</h2>"
                         f"<table class='log'><tr><th>Day</th><th>Attempts</th>"
                         f"<th>Passed</th></tr>{cells}</table>")
            wn, wok, wdays = week["n"] or 0, week["ok"] or 0, week["days"] or 0
            acc = f"{round(100 * wok / wn)}%" if wn else "—"
            parts.append(
                "<h2 id='week'>This week</h2>"
                f"<p>{wn} attempts across {wdays} active day"
                f"{'s' if wdays != 1 else ''} · {wok} passed "
                f"({acc}) — your weekly review ritual: wins, weak spots, "
                f"next week on the <a href='/due'>Due</a> queue.</p>")
        parts.append("<h2 id='attempts'>Attempts</h2>"
                         "<p id='timestamps'><small>Relative times "
                         "(“just now”, “3h ago”) — hover any time for "
                         "the exact timestamp.</small></p>")
        for r in rows:
            cls = "ok" if (r["grade"] or 0) >= 4 else "stale"
            mark = "✓" if (r["grade"] or 0) >= 4 else "✗"
            parts.append(
                f"<p class='{cls}'>{mark} {html.escape(r['concept'] or '')} — "
                f"grade {r['grade']}/5, confidence {r['confidence']}/5 "
                f"<small>{_rel_time(r['reviewed_at'] or '')}</small><br>"
                f"<small>in <a href='/modules/{r['module_id']}'>"
                f"{html.escape(r['summary'] or r['module_id'])}</a></small></p>")
        return "".join(parts)

    # Thin delegation: the real renderers live in focused modules
    # (exports.py, api.py, sitemap.py) per the Batch 3 modularity rule.
    def anki_tsv(self) -> str:
        return expmod.anki_tsv(self.db_path)

    def api_modules(self) -> str:
        return apimod.modules_json(self.db_path)

    def api_due(self) -> str:
        return apimod.due_json(self.db_path)

    def reviews_csv(self) -> str:
        return expmod.reviews_csv(self.db_path)

    def feed_xml(self, base_url: str) -> str:
        return expmod.feed_xml(self.db_path, base_url)

    def sitemap_xml(self, base_url: str) -> str:
        return sitemapmod.sitemap_xml(self.db_path, base_url)

    def robots_txt(self, base_url: str) -> str:
        return sitemapmod.robots_txt(base_url)

    def diagnose_html(self, trace: str = "") -> str:
        """Paste-a-traceback bridge: mentioned symbols → their lessons."""
        form = ("<form method='post' action='/diagnose' id='diagnose-form'>"
                "<textarea name='trace' rows='8' cols='70' placeholder='Paste a Python traceback…'>"
                f"{html.escape(trace)}</textarea><br>"
                "<button>Find my lessons</button></form>")
        if not trace.strip():
            return (form + "<p><small>Paste the red text from a crash — "
                    "every function it names links to its lesson.</small></p>")
        names = _trace_symbols(trace)
        if not names:
            return form + "<p>No function names found in that text.</p>"
        con = self._con()
        try:
            found = []
            missing = []
            for n in names:
                row = con.execute(
                    "SELECT concepts.id, concepts.name, concepts.module_id,"
                    " modules.task_summary FROM concepts"
                    " JOIN modules ON modules.id = concepts.module_id"
                    " WHERE concepts.name = ? LIMIT 1", (n,)).fetchone()
                (found if row else missing).append((n, row))
        finally:
            con.close()
        parts = [form, "<h2>Study these, then diagnose</h2>"]
        for n, row in found:
            node = row["id"].split(":", 1)[1] if ":" in row["id"] else row["id"]
            parts.append(
                f"<p><a href='/modules/{row['module_id']}#lesson-{_slug(node)}'>"
                f"{html.escape(n)}</a> "
                f"<small>in {html.escape(row['task_summary'] or row['module_id'])}</small></p>")
        if missing:
            parts.append("<p><small>Unknown here: "
                         + ", ".join(html.escape(n) for n, _ in missing)
                         + "</small></p>")
        return "".join(parts)

    def debt_html(self) -> str:
        """Comprehension debt: what changed vs what you can prove you own."""
        con = self._con()
        try:
            mods = con.execute(
                "SELECT id, repo, task_summary FROM modules"
                " ORDER BY created_at DESC").fetchall()
            per_repo: dict[str, dict[str, list]] = {}
            for m in mods:
                omap = _owned_map(con, m["id"])
                rows = con.execute(
                    "SELECT id, file FROM concepts WHERE module_id=?",
                    (m["id"],)).fetchall()
                bucket = per_repo.setdefault(m["repo"] or "(unknown repo)", {})
                for r in rows:
                    cell = bucket.setdefault(r["file"] or "(unknown)", [0, 0])
                    cell[1] += 1
                    if omap.get(r["id"], (0, False))[1]:
                        cell[0] += 1
        finally:
            con.close()
        if not per_repo:
            return ("<p>No modules yet — debt is zero because nothing "
                    "has changed.</p>")
        total_o = sum(c[0] for b in per_repo.values() for c in b.values())
        total_n = sum(c[1] for b in per_repo.values() for c in b.values())
        debt = 0 if not total_n else int(round(100 * (1 - total_o / total_n)))
        parts = [f"<div class='bar' id='debt-meter' role='img' aria-label='{debt}% "
                   f"comprehension debt'><i style='width:{debt}%'></i></div>"
                   f"<p><strong>{debt}% comprehension debt</strong> "
                   f"({total_o}/{total_n} concepts owned)</p>"]
        for repo in sorted(per_repo):
            parts.append(f"<h2>{html.escape(repo)}</h2>")
            files = sorted(per_repo[repo].items(),
                           key=lambda kv: (kv[1][0] / kv[1][1] if kv[1][1] else 1))
            cells = "".join(
                f"<tr><td>{html.escape(f)}</td><td>{o}/{n}</td>"
                f"<td>{int(round(100 * (1 - o / n))) if n else 0}%</td></tr>"
                for f, (o, n) in files)
            parts.append("<table class='log'><tr><th>File</th><th>Owned</th>"
                         "<th>Debt</th></tr>" + cells + "</table>")
        return "".join(parts)

    def projects_html(self) -> str:
        """Projects landing: every repo with modules, newest activity first."""
        con = self._con()
        try:
            mods = con.execute(
                "SELECT id, repo, task_summary, created_at FROM modules"
                " ORDER BY created_at DESC").fetchall()
            stats: dict[str, list] = {}
            for m in mods:
                omap = _owned_map(con, m["id"])
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

    def modules_html(self, repo: str = "", sort: str = "newest") -> str:
        """The library: every MCP session as a module card with progress."""
        if sort not in ("newest", "oldest"):
            sort = "newest"
        con = self._con()
        try:
            mods = con.execute(
                "SELECT id, task_summary, created_at, repo, commit_range FROM modules"
                " ORDER BY created_at DESC, rowid DESC LIMIT 50").fetchall()
            cards = []
            for m in mods:
                stats = con.execute(
                    "SELECT COUNT(*) AS n,"
                    " SUM(cards.stale) AS stale FROM concepts"
                    " LEFT JOIN cards ON cards.concept_id = concepts.id"
                    " WHERE concepts.module_id=?", (m["id"],)).fetchone()
                omap = _owned_map(con, m["id"])
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
                        "<p>No modules for this project yet.</p>")
            return ("<p>No modules yet. Finish an agent session with the "
                    "`create_learning_module` MCP tool and it appears here.</p>")
        if sort == "oldest":
            cards = cards[::-1]
        parts = []
        if repo:
            parts.append(f"<p class='crumbs'><a href='/'>Projects</a> › "
                         f"{html.escape(repo)}</p>")
        other = "oldest" if sort == "newest" else "newest"
        qs = f"?sort={other}" + (f"&repo={quote(repo, safe='')}" if repo else "")
        here = f"<b>{sort.title()}</b>"
        there = f"<a href='/modules{qs}'>{other.title()}</a>"
        first, second = (here, there) if sort == "newest" else (there, here)
        parts.append(f"<p id='sort'><small>Sort: {first} · {second}</small></p>")
        parts.append("<div id='library'>")
        for mi, (m, stats, omap, order) in enumerate(cards):
            n = stats["n"] or 0
            stale = stats["stale"] or 0
            owned_n = sum(1 for _, o in omap.values() if o)
            total = len(omap)
            pct = int(round(100 * owned_n / total)) if total else 0
            chips = f"<span class='chip'>{n} concept{'s' if n != 1 else ''}</span>"
            if stale:
                chips += f" <span class='chip'>{stale} stale</span>"
            target = _first_unowned(omap, order)
            rid = " id='resume'" if mi == 0 else ""
            if target is not None:
                node = target.split(":", 1)[1] if ":" in target else target
                resume = (f"<p><a class='btn'{rid} "
                          f"href='/modules/{m['id']}#lesson-{_slug(node)}'>Resume</a></p>")
            else:
                resume = (f"<p><a class='btn'{rid} href='/modules/{m['id']}'>"
                          f"Review again</a></p>")
            parts.append(
                f"<a class='modcard' href='/modules/{m['id']}'>"
                f"<h3>{html.escape(m['task_summary'] or m['id'])}</h3>"
                f"<small>{html.escape(m['created_at'] or '')}</small>"
                f"<div class='bar' aria-hidden='true'><i style='width:{pct}%'></i></div>"
                f"<p><small>{owned_n}/{total} concepts owned</small> {chips}</p></a>"
                f"{resume}")
        parts.append("<p id='exports'><small>Export: <a href='/export/anki.tsv'>Anki TSV</a> · "
                     "<a href='/feed.xml'>RSS feed</a></small></p>")
        parts.append("</div>")
        return "".join(parts)

    def _stored_lessons(self, con, card_ids: list[str]) -> dict:
        """(lesson dict, mastery) per card from lessons stored at creation."""
        if not card_ids:
            return {}
        rows = con.execute(
            "SELECT cards.id AS card, cards.concept_id AS cid, modules.lessons,"
            " concepts.mastery AS mastery"
            " FROM cards JOIN concepts ON concepts.id = cards.concept_id"
            " JOIN modules ON modules.id = concepts.module_id"
            f" WHERE cards.id IN ({','.join('?' * len(card_ids))})",
            card_ids).fetchall()
        out = {}
        for r in rows:
            try:
                lessons = {L["concept_id"]: L for L in json.loads(r["lessons"] or "[]")}
            except ValueError:
                continue
            node = r["cid"].split(":", 1)[1] if ":" in r["cid"] else r["cid"]
            if node in lessons:
                out[r["card"]] = (lessons[node], r["mastery"] or 0.0)
        return out

    def _attempts(self, con, card_ids: list[str]) -> dict:
        if not card_ids:
            return {}
        rows = con.execute(
            "SELECT card_id, COUNT(*) AS n FROM reviews"
            f" WHERE card_id IN ({','.join('?' * len(card_ids))})"
            " GROUP BY card_id", card_ids).fetchall()
        return {r["card_id"]: r["n"] for r in rows}

    def _history_by_card(self, con, mid: str) -> dict:
        """Past reviews per card for one module, newest first."""
        try:
            rows = con.execute(
                "SELECT reviews.card_id, reviews.grade, reviews.confidence,"
                " reviews.reviewed_at, reviews.submission FROM reviews"
                " JOIN cards ON cards.id = reviews.card_id"
                " JOIN concepts ON concepts.id = cards.concept_id"
                " WHERE concepts.module_id=? ORDER BY reviews.id DESC",
                (mid,)).fetchall()
        except Exception:  # noqa: BLE001 — pre-migration DBs lack submission
            rows = con.execute(
                "SELECT reviews.card_id, reviews.grade, reviews.confidence,"
                " reviews.reviewed_at FROM reviews"
                " JOIN cards ON cards.id = reviews.card_id"
                " JOIN concepts ON concepts.id = cards.concept_id"
                " WHERE concepts.module_id=? ORDER BY reviews.id DESC",
                (mid,)).fetchall()
            rows = [dict(r, submission="") for r in rows]
            out = {}
            for r in rows:
                out.setdefault(r["card_id"], []).append(r)
            return out
        out = {}
        for r in rows:
            out.setdefault(r["card_id"], []).append(dict(r))
        return out

    def _submissions_html(self, entries: list[dict]) -> str:
        """Submission history beneath a lesson's exercises."""
        if not entries:
            return "<p><small>No attempts yet — your tries will appear here.</small></p>"
        items = []
        for e in entries[:10]:
            good = (e.get("grade") or 0) >= 4
            cls = "ok" if good else "stale"
            mark = "✓" if good else "✗"
            sub = (e.get("submission") or "").strip()
            excerpt = html.escape(sub[:200] + ("…" if len(sub) > 200 else ""))
            if not sub:
                excerpt = "<i>no text recorded</i>"
            items.append(
                f"<p class='{cls}'><small>{mark} grade {e.get('grade')}/5,"
                f" confidence {e.get('confidence')}/5,"
                f" {html.escape(e.get('reviewed_at') or '')}<br>"
                f"tried: <code>{excerpt}</code></small></p>")
        more = (f"<p><small>…and {len(entries) - 10} more.</small></p>"
                if len(entries) > 10 else "")
        return ("<details><summary>Past attempts "
                f"({len(entries)})</summary>{''.join(items)}{more}</details>")

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
            tries = self._attempts(con, [c["id"] for c in cards])
            history = self._history_by_card(con, mid)
            owned = _owned_map(con, mid)
            ladders = _bloom_reached(con, mid)
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
        parts = [f"<p class='crumbs'><a href='/modules'>Modules</a> › "
                   f"{html.escape(m['task_summary'] or mid)}</p>",
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
        toc = []
        for row in concepts:
            node = row["cid"].split(":", 1)[1] if ":" in row["cid"] else row["cid"]
            toc.append(f"<a href='#lesson-{_slug(node)}'>{html.escape(row['name'])}</a>")
        if toc:
            parts.append(f"<p class='toc'><small>In this module: {' · '.join(toc)}</small></p>")
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
        for ci, row in enumerate(concepts):
            node = row["cid"].split(":", 1)[1] if ":" in row["cid"] else row["cid"]
            slug = _slug(node)
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
                f" <span class='chip'>{status}</span>"
                f"{_ladder_html(ladders.get(row['cid'], -1), ladder_extra)}{stale}</h2>"
                f"<p><small>{html.escape(row['kind'])} · "
                f"{html.escape(row['file'])}:{row['line']}</small></p>")
            if node in lesson_map:
                parts.append(render_levels(
                    lesson_map[node], mastery_of[node], concept_tries,
                    level, base))
            if concept_cards:
                if not practice_tagged:
                    parts.append("<h3 id='practice'>Practice</h3>")
                    practice_tagged = True
                else:
                    parts.append("<h3>Practice</h3>")
            for c in concept_cards:
                lesson = (f"<details><summary>Study first — explained your way</summary>"
                          f"{render_levels(lesson_map[node], mastery_of.get(node, 0.0), tries.get(c['id'], 0), level, base)}</details>"
                          if node in lesson_map else "")
                parts.append(
                    f"<article><h3>{html.escape(c['concept'])} "
                    f"{_difficulty_dots(c['difficulty'])}</h3>"
                    f"{lesson}"
                    f"{why_html(c)}"
                    f"<p>{html.escape(c['front'])}</p>"
                    f"{answer_widget(c, tries.get(c['id'], 0), base)}"
                    f"{self._submissions_html(history.get(c['id'], []))}</article>")
            parts.append("</section>")
        parts.append("<a class='totop' href='#top'>Back to top ↑</a>")
        return "".join(parts)

    def _tour_targets(self) -> tuple[str, str]:
        """(latest module id, its first lesson anchor) for tour deep links."""
        con = self._con()
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
        return mid, f"lesson-{_slug(node)}"

    def tour_html(self) -> str:
        """Catalog of every web-facing item, each with a Show-me link."""
        mid, lesson = self._tour_targets()
        parts = ["<p>Every capability below has a visible home. "
                 "<b>Show me</b> jumps to it and highlights it; "
                 "Prev/Next walks the whole list.</p>",
                 f"<p><a class='btn' href='{tourmod.step_url(tourmod.ORDER[0], mid, lesson)}'>"
                 "Start guided tour</a></p>"]
        groups = (("mvp", "The loop", "The original learning cycle."),
                  ("feature", "Features", "New capabilities, Batch 1."),
                  ("improvement", "Improvements", "Batch 1 friction removal."))
        n = 0
        for kind, heading, sub in groups:
            items = [e for e in tourmod.ENTRIES if e["kind"] == kind]
            lis = []
            for e in items:
                n += 1
                url = tourmod.step_url(e["id"], mid, lesson)
                lis.append(
                    f"<li><b>{n}. {html.escape(e['title'])}</b> — "
                    f"{html.escape(e['blurb'])} "
                    f"<a class='btn' href='{url}'>Show me</a></li>")
            parts.append(
                f"<h2>{heading}</h2><p><small>{sub}</small></p>"
                f"<ol class='tour-steps' start='{n - len(items) + 1}'>"
                + "".join(lis) + "</ol>")
        return "".join(parts)

    def status_html(self) -> str:
        """Visible home for the non-page items: CI, hooks, CLI, MCP, exports."""
        root = Path(__file__).resolve().parent.parent
        ci = root / ".github" / "workflows" / "groundwork.yml"
        hook = root / "hooks" / "pre-commit"
        now = schedmod.iso(schedmod.utcnow())
        con = self._con()
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
            "loads it into another database. Reviews stay private; scheduling restarts fresh.</p>",
            "<h2 id='status-modular'>Module health</h2>" +
            modularitymod.status_rows() +
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
        if url.path == "/diagnose":
            form = parse_qs(raw, keep_blank_values=True)
            trace = (form.get("trace", [""])[0] or "")[:20000]
            body = self.diagnose_html(trace)
            self._send(page("Diagnose", body, active="due", page_id="due",
                            lede="Paste a traceback — study first, then fix.",
                            counts=self._nav_counts()))
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
            body = render_result(res["pass"], res["feedback"], back,
                                 out["next_due"], origin, mod_id, due_left)
            self._send(page("Result", body, counts=self._nav_counts()))
            return
        self._send(b"not found", 404, "text/plain")


def serve(host: str = "127.0.0.1", port: int = 8765, db_path: str = "groundwork.db"):
    dbmod.init_db(db_path)
    Handler.db_path = db_path
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Groundwork UI at http://{host}:{port}/ (db: {db_path})")
    httpd.serve_forever()


def render_exercise_preview(exercise: dict) -> str:
    return exmod.render(exercise)


def check_stale(db_path: str, repo: str) -> int:
    con = dbmod.connect(db_path)
    try:
        return modmod.mark_stale_cards(con, repo)
    finally:
        con.close()
