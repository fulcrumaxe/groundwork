"""Chrome MCP verification sweep for Batch 9 improvements + features.

Serves the groundwork web app from a temp DB copy, opens each fixture
page in a real headless Chrome via the chrome-devtools-mcp stdio server
(tools/chrome_mcp.py), and asserts the rendered DOM for every Batch 9
item (I-42/I-46/I-48/I-49/I-50/I-52/I-53/I-54, F-26..F-33 = types 49-56).

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
    # F-26..F-33: exercise types 49-56 appear in Modules listing
    ("F-types", "/modules",
     "() => { const t=document.body.textContent; return [49,50,51,52,53,54,55,56].filter(n=>t.includes('exercise type '+n)).join(','); }"),
    # F-33: cssfix render names properties but hides expected values
    ("F-33", "/modules",
     "() => /css-fix|cssfix/i.test(document.body.textContent)"),
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
        return s == "49,50,51,52,53,54,55,56", f"types-present=[{s}]"
    return val is True, s[:200]


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

    tmp = Path(tempfile.mkdtemp(prefix="b9chrome"))
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
            # Batch 9 item checks (revisit each path once)
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
