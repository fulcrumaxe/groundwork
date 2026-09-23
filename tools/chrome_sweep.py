"""Chrome MCP verification sweep for Batch 13 improvements + features.

Serves the groundwork web app from a temp DB copy, opens each fixture
page in a real headless Chrome via the chrome-devtools-mcp stdio server
(tools/chrome_mcp.py), and asserts the rendered DOM for every Batch 13
item (I-83..I-90, F-60..F-67). Batch 9/10/11/12 checks are kept
so the sweep still guards the previous batches' surfaces. Ends with a
live interaction: one real card review submitted on /due (verdict page
proves the grade + collapse/undo flow), or the done-hero when the queue
is empty.

Usage:
  python3 tools/chrome_sweep.py [--shot-dir DIR] [--keep] [--port N]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from chrome_mcp import MCPClient  # noqa: E402

MCPError = Exception

FIXTURES = [
    ("projects", "/"),
    ("due", "/due"),
    ("modules", "/modules"),
    ("reviews", "/reviews"),
    ("status", "/status"),
]

CHECKS: list[tuple[str, str, str]] = [
    # I-42: collapse answered-due cards in place with undo
    ("I-42", "/due",
     "() => !!document.querySelector('[data-collapse],.collapse-toggle,.answered-collapse,details.answered,#collapse-undo') || /collapse/i.test(document.body.innerHTML)"),
    # I-46: one-click 5-minute session queue on the Due page
    ("I-46", "/due",
     "() => { const s=document.querySelector('#minisession'); return s ? s.textContent : ''; }"),
    # I-48: resume interrupted sessions from History (seeded attempt)
    ("I-48", "/reviews",
     "() => { const a=[...document.querySelectorAll('a')].find(e=>/\\/due\\?resume=/.test(e.href)); return a ? a.href : ''; }"),
    # I-49: URL-based session share snapshot link
    ("I-49", "/status",
     "() => /snapshot|share/i.test(document.body.textContent)"),
    # I-50: quarterly link audit as automated test (status surface)
    ("I-50", "/status",
     "() => /link.?audit|linkcheck|links ok|broken link/i.test(document.body.textContent)"),
    # I-52: dark mode via prefers-color-scheme
    ("I-52", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return /prefers-color-scheme\\s*:\\s*dark/.test(css); }"),
    # I-53: type scale display h1-h4/body/small/code
    ("I-53", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return ['--fs-display','--fs-h1','--fs-h2','--fs-h3','--fs-h4','--fs-body','--fs-small','--fs-code'].filter(v=>css.includes(v)).join(','); }"),
    # I-54: offline-safe font pairing (system font stack, no remote fonts)
    ("I-54", "/",
     "() => { const b=getComputedStyle(document.body).fontFamily||''; return (b.includes('Segoe UI')||b.includes('system')) + '|' + !/fonts\\.googleapis/.test(document.documentElement.innerHTML); }"),
    # F-26..F-33: exercise types 49-56 render anchored status sections.
    # (Deterministic registry hooks, Batch-10 precedent: the old
    # Modules-listing text rotted once 124 modules paginated the Batch-9
    # summaries carrying those strings off page 1.)
    ("F-types", "/status",
     "() => ['status-b9-threatmodel','status-b9-secretscan','status-b9-inputaudit','status-b9-a11yaudit','status-b9-i18n','status-b9-regexex','status-b9-sqlex','status-b9-cssfix'].filter(a=>!document.querySelector('#'+a)).join(',')"),
    # F-33: cssfix status section renders (names-properties/hides-values
    # is pinned by test_render_hides_expected_values).
    ("F-33", "/status",
     "() => !!document.querySelector('#status-b9-cssfix')"),
    # Batch 10 improvements (I-55..I-62)
    # I-55: inline SVG wordmark in every page header
    ("I-55", "/",
     "() => !!document.querySelector('h1 svg.wordmark')"),
    # I-56: tier chips in the Batch 10 status section (8 since Batch 18 adds understand)
    ("I-56", "/status",
     "() => document.querySelectorAll('.chip[class*=\"bloom-\"]').length"),
    # I-57: progress width transition in the head wire
    ("I-57", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('.bar i{transition:width'); }"),
    # I-58: live Owned badge sample in the Batch 10 status section
    ("I-58", "/status",
     "() => !!document.querySelector('.owned-badge')"),
    # I-59: card stagger keyframe in the head wire
    ("I-59", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('gw-card-in'); }"),
    # I-60: disclosure caret rules in the head wire
    ("I-60", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('summary::before'); }"),
    # I-61: line-number counter rules in the head wire
    ("I-61", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('counter(codeline)'); }"),
    # I-62: live highlight demo in the Batch 10 status section
    ("I-62", "/status",
     "() => !!document.querySelector('.tok-keyword')"),
    # Batch 10 features: one anchored section per new exercise type.
    # (The Modules listing reflects DB cards, not the registry, so the
    # deterministic per-type hook is the status anchor; registry
    # coverage for types 57-64 is pinned by test_all_types_generate.)
    ("F-57", "/status",
     "() => !!document.querySelector('#status-b10-cliux')"),
    ("F-58", "/status",
     "() => !!document.querySelector('#status-b10-logread')"),
    ("F-59", "/status",
     "() => !!document.querySelector('#status-b10-metrics')"),
    ("F-60", "/status",
     "() => !!document.querySelector('#status-b10-flame')"),
    ("F-61", "/status",
     "() => !!document.querySelector('#status-b10-crashdump')"),
    ("F-62", "/status",
     "() => !!document.querySelector('#status-b10-depupgrade')"),
    ("F-63", "/status",
     "() => !!document.querySelector('#status-b10-licensecheck')"),
    ("F-64", "/status",
     "() => !!document.querySelector('#status-b10-containerize')"),
    # Batch 11 improvements (I-63..I-70): status anchor + head-wire token
    ("I-63", "/status",
     "() => !!document.querySelector('#status-b11-hinttiers')"),
    ("I-63-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('.hint-nudge'); }"),
    ("I-64", "/status",
     "() => !!document.querySelector('#status-b11-confslider')"),
    ("I-64-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('.confslider'); }"),
    ("I-65", "/status",
     "() => !!document.querySelector('#status-b11-focusrings')"),
    ("I-65-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('--focus-ring'); }"),
    ("I-66", "/status",
     "() => !!document.querySelector('#status-b11-taptargets')"),
    ("I-66-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('--tap-min'); }"),
    ("I-67", "/status",
     "() => !!document.querySelector('#status-b11-radius')"),
    ("I-67-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('--r-card'); }"),
    ("I-68", "/status",
     "() => !!document.querySelector('#status-b11-spacing')"),
    ("I-68-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('--sp-section'); }"),
    ("I-69", "/status",
     "() => !!document.querySelector('#status-b11-emptyart')"),
    ("I-70", "/status",
     "() => !!document.querySelector('#status-b11-donehero')"),
    # Batch 11 features: one anchored section per new exercise type.
    ("F-65", "/status",
     "() => !!document.querySelector('#status-b11-cipipe')"),
    ("F-66", "/status",
     "() => !!document.querySelector('#status-b11-flagcut')"),
    ("F-67", "/status",
     "() => !!document.querySelector('#status-b11-backfill')"),
    ("F-68", "/status",
     "() => !!document.querySelector('#status-b11-pageapi')"),
    ("F-69", "/status",
     "() => !!document.querySelector('#status-b11-cacheinv')"),
    ("F-70", "/status",
     "() => !!document.querySelector('#status-b11-idempot')"),
    ("F-71", "/status",
     "() => !!document.querySelector('#status-b11-ratelimit')"),
    ("F-72", "/status",
     "() => !!document.querySelector('#status-b11-webhook')"),
    # Batch 12 improvements (I-71..I-82): status anchor + head-wire token.
    # (B12- prefix: sweep F-57..F-59 names belong to exercise types.)
    ("B12-I71", "/status",
     "() => !!document.querySelector('#status-b12-logbook')"),
    ("B12-I71-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('table.log td{border-bottom'); }"),
    ("B12-I72", "/status",
     "() => !!document.querySelector('#status-b12-shelf')"),
    ("B12-I72-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('--shelf-spine'); }"),
    ("B12-I73", "/status",
     "() => !!document.querySelector('#status-b12-briefing')"),
    ("B12-I73-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('counter-reset:mission'); }"),
    ("B12-I77", "/status",
     "() => !!document.querySelector('#status-b12-verdicts')"),
    ("B12-I77-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('.verdict-stamp'); }"),
    ("B12-I79", "/status",
     "() => !!document.querySelector('#status-b12-ownbanner')"),
    ("B12-I79-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('.ownbanner'); }"),
    ("B12-I80", "/status",
     "() => !!document.querySelector('#status-b12-pressfx')"),
    ("B12-I80-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('scale(0.97)'); }"),
    ("B12-I81", "/status",
     "() => !!document.querySelector('#status-b12-skeletons')"),
    ("B12-I81-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('gw-sk-pulse'); }"),
    ("B12-I82", "/status",
     "() => !!document.querySelector('#status-b12-optimistic')"),
    ("B12-I82-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('.gw-spinner'); }"),
    ("B12-I82-js", "/due",
     "() => !!document.querySelector('script[data-optimistic-submit]')"),
    # Batch 12 features (F-50..F-59): one anchored section each.
    ("B12-F50", "/status",
     "() => !!document.querySelector('#status-b12-typecontract')"),
    ("B12-F51", "/status",
     "() => !!document.querySelector('#status-b12-retest')"),
    ("B12-F54", "/status",
     "() => !!document.querySelector('#status-b12-quests')"),
    ("B12-F55", "/status",
     "() => !!document.querySelector('#status-b12-diffdial')"),
    ("B12-F56", "/status",
     "() => !!document.querySelector('#status-b12-coldattempt')"),
    ("B12-F57", "/status",
     "() => !!document.querySelector('#status-b12-fading')"),
    ("B12-F58", "/status",
     "() => !!document.querySelector('#status-b12-selfexplain')"),
    ("B12-F59", "/status",
     "() => !!document.querySelector('#status-b12-elaboration')"),
    # Batch 13 improvements (I-83..I-90): status anchor + head-wire token.
    ("B13-I83", "/status",
     "() => !!document.querySelector('#status-b13-errpage')"),
    ("B13-404", "/nope-b13",
     "() => !!document.querySelector('#sitenav') && !!document.querySelector('#not-found')"),
    ("B13-I84", "/status",
     "() => !!document.querySelector('#status-b13-formerr')"),
    ("B13-I84-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('.field-error'); }"),
    ("B13-I85", "/status",
     "() => !!document.querySelector('#status-b13-selection')"),
    ("B13-I85-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('::selection'); }"),
    ("B13-I86", "/status",
     "() => !!document.querySelector('#status-b13-scrollbar')"),
    ("B13-I86-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('scrollbar-width'); }"),
    ("B13-I87", "/status",
     "() => !!document.querySelector('#status-b13-pageicon')"),
    ("B13-I87-link", "/",
     "() => { const l=document.querySelector(\"link#gw-icon[rel='icon']\"); return l ? l.href.slice(0,22) : ''; }"),
    ("B13-I88", "/status",
     "() => !!document.querySelector('#status-b13-ogtags')"),
    ("B13-I88-meta", "/",
     "() => { const m=document.querySelector(\"meta[property='og:title']\"); return m ? m.content : ''; }"),
    ("B13-I89", "/status",
     "() => !!document.querySelector('#status-b13-density')"),
    ("B13-I89-btn", "/",
     "() => !!document.querySelector('#gw-density-toggle')"),
    ("B13-I89-js", "/due",
     "() => !!document.querySelector('script[data-density-toggle]')"),
    ("B13-I89-click", "/",
     "() => { const b=document.querySelector('#gw-density-toggle'); if(!b) return 'no-button'; b.click(); return document.documentElement.getAttribute('data-density')||'unset'; }"),
    ("B13-I90", "/status",
     "() => !!document.querySelector('#status-b13-responsive')"),
    ("B13-I90-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('max-width:640px'); }"),
    # Batch 13 features (F-60..F-67): one anchored section each.
    ("B13-F60", "/status",
     "() => !!document.querySelector('#status-b13-dualcode')"),
    ("B13-F61", "/status",
     "() => !!document.querySelector('#status-b13-interleave')"),
    ("B13-F62", "/status",
     "() => !!document.querySelector('#status-b13-spacingopt')"),
    ("B13-F63", "/status",
     "() => !!document.querySelector('#status-b13-retrieval')"),
    ("B13-F64", "/status",
     "() => !!document.querySelector('#status-b13-predict')"),
    ("B13-F65", "/status",
     "() => !!document.querySelector('#status-b13-confweight')"),
    ("B13-F66", "/status",
     "() => !!document.querySelector('#status-b13-calibdrill')"),
    ("B13-F67", "/status",
     "() => !!document.querySelector('#status-b13-overconf')"),
    # Batch 19 improvements (I-104..I-109, I-112, I-115): status anchor
    # plus the live sample marker each section renders below it.
    ("B19-I104", "/status",
     "() => !!document.querySelector('#status-b19-symlinks') && !!document.querySelector('.symlink')"),
    ("B19-I105", "/status",
     "() => !!document.querySelector('#status-b19-replay') && /Step 2 of 3/.test(document.querySelector('#replay') ? document.querySelector('#replay').textContent : '')"),
    ("B19-I106", "/status",
     "() => !!document.querySelector('#status-b19-runinputs') && !!document.querySelector('#runinputs')"),
    ("B19-I107", "/status",
     "() => !!document.querySelector('#status-b19-beforafter') && /Show what changed/.test(document.body.textContent)"),
    ("B19-I108", "/status",
     "() => !!document.querySelector('#status-b19-srccollapse') && !!document.querySelector('.srccollapse')"),
    ("B19-I109", "/status",
     "() => !!document.querySelector('#status-b19-whyit') && !!document.querySelector('.lesson-why')"),
    ("B19-I112", "/status",
     "() => !!document.querySelector('#status-b19-tryprompts') && !!document.querySelector('#tryprompts')"),
    ("B19-I115", "/status",
     "() => !!document.querySelector('#status-b19-lessonver') && !!document.querySelector('.lessonver')"),
    ("B19-I115-css", "/",
     "() => { const css=[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n'); return css.includes('.lessonver'); }"),
    # Batch 19 features (F-77..F-84): one anchored section each.
    ("B19-F77", "/status",
     "() => !!document.querySelector('#status-b19-apiguess')"),
    ("B19-F78", "/status",
     "() => !!document.querySelector('#status-b19-modelmap')"),
    ("B19-F79", "/status",
     "() => !!document.querySelector('#status-b19-rubberduck')"),
    ("B19-F80", "/status",
     "() => !!document.querySelector('#status-b19-protege')"),
    ("B19-F81", "/status",
     "() => !!document.querySelector('#status-b19-feynman')"),
    ("B19-F82", "/status",
     "() => !!document.querySelector('#status-b19-analogy')"),
    ("B19-F83", "/status",
     "() => !!document.querySelector('#status-b19-counterex')"),
    ("B19-F84", "/status",
     "() => !!document.querySelector('#status-b19-boundary')"),
    # Batch 21 improvements (I-92, I-126, I-127, I-130-I-132, I-134):
    # one anchored section each.
    ("B21-I92", "/status",
     "() => !!document.querySelector('#status-b21-tablescroll')"),
    ("B21-I126", "/status",
     "() => !!document.querySelector('#status-b21-callgraph')"),
    ("B21-I127", "/status",
     "() => !!document.querySelector('#status-b21-seqdiag')"),
    ("B21-I130", "/status",
     "() => !!document.querySelector('#status-b21-imgattach')"),
    ("B21-I131", "/status",
     "() => !!document.querySelector('#status-b21-lessondeps')"),
    ("B21-I132", "/status",
     "() => !!document.querySelector('#status-b21-depcycle')"),
    ("B21-I134", "/status",
     "() => !!document.querySelector('#status-b21-confusing')"),
    # Batch 21 features (F-93..F-100): one anchored section each,
    # plus the live samples the atoms/remediation sections render.
    ("B21-F93", "/status",
     "() => !!document.querySelector('#status-b21-sleepsched')"),
    ("B21-F94", "/status",
     "() => !!document.querySelector('#status-b21-cogniload')"),
    ("B21-F95", "/status",
     "() => !!document.querySelector('#status-b21-flowdetect')"),
    ("B21-F96", "/status",
     "() => !!document.querySelector('#status-b21-frustcatch')"),
    ("B21-F97", "/status",
     "() => !!document.querySelector('#status-b21-boredom')"),
    ("B21-F98", "/status",
     "() => !!document.querySelector('#status-b21-stylemix')"),
    ("B21-F99", "/status",
     "() => !!document.querySelector('#status-b21-skillatoms')"),
    ("B21-F99-sample", "/status",
     "() => !!document.querySelector('#status-b21-skillatoms') && !!document.querySelector('#skill-atoms')"),
    ("B21-F100", "/status",
     "() => !!document.querySelector('#status-b21-remedpath')"),
    ("B21-F100-sample", "/status",
     "() => !!document.querySelector('#status-b21-remedpath') && !!document.querySelector('.remediation')"),
]


def unwrap_eval(text: str):
    """Extract the JS value from chrome-devtools-mcp's ```json fence."""
    m = re.search(r"```json\s*\n(.*?)```", text, re.S)
    payload = m.group(1).strip() if m else text.strip()
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return payload


def judge(item: str, val) -> tuple[bool, str]:
    """Per-item pass predicate over the unwrapped JS value."""
    s = str(val)
    if item == "I-46":
        ok = "Start" in s and "minute" in s
        return ok, s[:200]
    if item == "I-48":
        return bool(s.strip()), s[:200] or "no /due?resume= link"
    if item == "I-53":
        toks = [t for t in s.split(",") if t]
        return len(toks) == 8, s[:200]
    if item == "I-54":
        return s == "true|true", s[:200]
    if item == "F-types":
        return s == "", f"types-missing=[{s}]" if s else "all-8-present"
    if item == "I-56":
        return s == "8", f"tier-chips=[{s}]"
    if item == "B13-I87-link":
        return s.startswith("data:image/svg+xml,"), s[:200]
    if item == "B13-I88-meta":
        return bool(s.strip()), s[:200] or "no og:title content"
    if item == "B13-I89-click":
        return s == "compact", s[:200]
    return val is True, s[:200]


def interact_review(c: MCPClient, base: str) -> tuple[bool, str]:
    """Submit one real card review on /due; verdict proves the flow.

    Fills the first review form (any exercise type: textarea, select,
    confidence default) and clicks submit. A verdict page proves
    grading + result render; an empty queue proves the done-hero (I-70)
    instead. Returns (pass, detail).
    """
    pid = visit(c, base + "/due")
    probe = unwrap_eval(eval_js(c, pid, "() => { const f = document.querySelector(\"form[action*='/review']\"); if (!f) return document.querySelector('#done-hero') ? 'empty-hero' : 'no-form'; const ta = f.querySelector('textarea'); if (ta) ta.value = 'sweep probe answer'; const sel = f.querySelector('select'); if (sel) sel.selectedIndex = sel.options.length - 1; const conf = f.querySelector(\"input[name='confidence'][value='4']\"); if (conf) conf.checked = true; const btn = f.querySelector('button'); if (!btn) return 'no-button'; btn.click(); return 'clicked'; }"))
    if probe == "empty-hero":
        return True, "empty queue renders #done-hero"
    if probe != "clicked":
        return False, f"review form not submittable ({probe})"
    deadline = time.time() + 30
    while time.time() < deadline:
        time.sleep(1.0)
        try:
            state = str(unwrap_eval(
                eval_js(c, pid, "() => document.readyState"))).strip()
            if state != "complete":
                continue
            body = str(unwrap_eval(eval_js(
                c, pid,
                "() => document.body.textContent.slice(0, 4000)"))).lower()
            undo = str(unwrap_eval(eval_js(
                c, pid,
                "() => !!document.querySelector(\"form[action='/reviews/undo']\")")))
        except Exception:
            continue
        if "verdict" in body or undo == "True":
            return True, "review submitted, verdict rendered"
    return False, "no verdict after submit"


def seed_attempt(db_path: str) -> None:
    """One graded attempt so History renders rows + resume links (I-48)."""
    con = sqlite3.connect(db_path)
    try:
        card = con.execute("SELECT id FROM cards LIMIT 1").fetchone()
        if card and not con.execute(
                "SELECT COUNT(*) FROM reviews").fetchone()[0]:
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence)"
                " VALUES(?,?,?)", (card[0], 2, 3))
            con.commit()
    finally:
        con.close()


def wait_for_server(base: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base + "/status", timeout=3) as r:
                if r.status == 200:
                    return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError(f"server at {base} did not come up")


def eval_js(c: MCPClient, pid: int, fn: str):
    res = c.call("evaluate_script", {"pageId": pid, "function": fn})
    out = []
    for item in res.get("content", []):
        if item.get("type") == "text":
            out.append(item.get("text", ""))
    return "\n".join(out)


def selected_page_id(c: MCPClient) -> int:
    res = c.call("list_pages", {})
    text = "\n".join(
        item.get("text", "") for item in res.get("content", [])
        if item.get("type") == "text")
    m = re.search(r"(\d+):[^\n]*\[selected\]", text)
    if not m:
        raise RuntimeError(f"no selected page in: {text[:300]}")
    return int(m.group(1))


def visit(c: MCPClient, url: str) -> int:
    print(f"[sweep] open {url}", flush=True)
    res = c.call("new_page", {"url": url}, timeout=60)
    if res.get("isError"):
        raise RuntimeError(f"new_page {url}: {json.dumps(res)[:300]}")
    pid = selected_page_id(c)
    deadline = time.time() + 45
    while time.time() < deadline:
        try:
            state = str(unwrap_eval(
                eval_js(c, pid, "() => document.readyState"))).strip()
            href = str(unwrap_eval(
                eval_js(c, pid, "() => location.href"))).strip()
        except Exception as e:
            print(f"[sweep]   eval retry: {e!r:.120}", flush=True)
            time.sleep(1.0)
            continue
        if state == "complete" and href.startswith("http"):
            print(f"[sweep]   ready page={pid} {href}", flush=True)
            return pid
        time.sleep(0.5)
    raise RuntimeError(f"page never ready: {url} (page {pid})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot-dir", default=None)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="b11chrome"))
    shot_dir = Path(args.shot_dir) if args.shot_dir else tmp / "shots"
    shot_dir.mkdir(parents=True, exist_ok=True)
    db_src = ROOT / "groundwork.db"
    db = tmp / "verify.db"
    shutil.copy(db_src, db)
    seed_attempt(str(db))

    server = subprocess.Popen(
        [sys.executable, "-m", "groundwork", "--db", str(db),
         "serve", "--port", str(args.port)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    base = f"http://127.0.0.1:{args.port}"
    failures: list[str] = []
    results: list[dict] = []
    try:
        wait_for_server(base)
        c = MCPClient(roots=[str(shot_dir)])
        try:
            seen: dict[str, dict] = {}
            # DOM/console/screenshot per fixture, one tab at a time
            for name, path in FIXTURES:
                pid = visit(c, base + path)
                title = unwrap_eval(eval_js(c, pid, "() => document.title"))
                errors = unwrap_eval(eval_js(
                    c, pid,
                    "() => (window.__errors||[]).join('\\n') || "
                    "Array.from(document.querySelectorAll('.error,.traceback')).map(e=>e.textContent.slice(0,200)).join('\\n') || 'none'",
                ))
                shot = shot_dir / f"{name}.jpeg"
                print(f"[sweep] shot {name} page={pid}", flush=True)
                shot_res = c.call("take_screenshot",
                                  {"pageId": pid, "filePath": str(shot)},
                                  timeout=60)
                if shot_res.get("isError") or not shot.exists():
                    raise RuntimeError(
                        f"screenshot {name}: {json.dumps(shot_res)[:300]}")
                ok = bool(str(title).strip()) and str(errors).strip() == "none"
                results.append({"kind": "fixture", "name": name,
                                "title": title, "console_errors": errors,
                                "shot": str(shot), "pass": ok})
                if not ok:
                    failures.append(f"fixture {name}: title={title!r} errors={errors!r}")
            # Batch 9/10/11 item checks (revisit each path once)
            for item, path, fn in CHECKS:
                if path not in seen:
                    seen[path] = visit(c, base + path)
                try:
                    val = unwrap_eval(eval_js(c, seen[path], fn))
                    ok, detail = judge(item, val)
                    results.append({"kind": "check", "item": item,
                                    "pass": ok, "detail": detail})
                    if not ok:
                        failures.append(f"{item}: check false ({detail})")
                except MCPError as e:
                    failures.append(f"{item}: eval error {e}")
                    results.append({"kind": "check", "item": item,
                                    "pass": False, "detail": str(e)})
            ok, detail = interact_review(c, base)
            results.append({"kind": "interact", "item": "review-submit",
                            "pass": ok, "detail": detail})
            if not ok:
                failures.append(f"review-submit: {detail}")
        finally:
            c.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except Exception:
            server.kill()
        if not args.keep:
            shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"results": results, "failures": failures}, indent=1))
    rep = tmp / "report.json" if args.keep else None
    if args.keep:
        (shot_dir / "report.json").write_text(
            json.dumps({"results": results, "failures": failures}, indent=1))
    print(f"checks passed: {sum(1 for r in results if r['pass'])}/{len(results)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
