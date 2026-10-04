"""Demo-video pipeline: 30-60s per-item mp4 from Chrome + terminal beats.

Each shipped improvement/feature gets one short video proving the full
behavior: Chrome beats show the live surface (Status anchor, History
report, Due review flow) while terminal beats show the code/CLI side
(MCP calls, pure-function output, DB state). Title cards open/close.

How it works (stdlib + chromium + ffmpeg, no new deps):
  1. copy groundwork.db to a temp fixture DB, run the scenario's
     seed_db() to manipulate data (backdated reviews, prior answers)
  2. serve the app from the fixture DB (same shape as chrome_sweep.py)
  3. drive headless Chrome via chrome-devtools-mcp: navigate pages,
     run interactions, inject a caption bar, screenshot each beat.
     Terminal/title beats render as local HTML and screenshot through
     the SAME client, so every frame is a real Chrome render.
  4. assemble the stills with ffmpeg concat (per-beat durations) into
     1280x720 H.264 mp4; ffprobe must read 30-60s or we fail.

Usage:
  python3 tools/demo_video.py --scenario answerhist [--out DIR] [--keep]
  nix run .#demo-video -- --scenario halflife --out demos/
  python3 tools/demo_video.py --list
"""
from __future__ import annotations

import argparse
import html
import importlib
import json
import os
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

WIDTH = 1280
HEIGHT = 720
FPS = 30
MIN_SECONDS = 30.0
MAX_SECONDS = 60.0
#: Retina capture (1280x720 CSS at 2x = 2560x1440 PNG); ffmpeg
#: downscales to 1280x720, so text renders supersampled-sharp.
VIEWPORT = "1280x720x2"
SHOT_WIDTH = 2560

BEAT_TYPES = ("title", "chrome", "terminal")


# ---------------------------------------------------------------- pure helpers

def total_duration(beats) -> float:
    """Sum of beat durations; unparseable beats count 0."""
    total = 0.0
    try:
        for beat in beats or []:
            try:
                total += float(beat.get("duration", 0))
            except (TypeError, ValueError, AttributeError):
                continue
    except Exception:
        return 0.0
    return total


def output_paths(out_dir, scn) -> tuple:
    """(mp4, gif, manifest, frames_dir) for a scenario.

    Organized by batch, kind, and item: <out>/batch-<N>/<kind>/
    <name>/ holds the three files plus the kept per-beat frames
    under <id>-frames/. <name> is "<id>-<I-N/F-N>" when the
    scenario declares a backlog number, else the bare scenario id
    (some early items, like the seed, were never filed).
    """
    kind = scn.get("kind", "")
    sid = scn.get("id", "scenario")
    item = scn.get("item")
    folder = f"{sid}-{item}" if item else sid
    sub = (out_dir / f"batch-{scn.get('batch', '?')}" / kind / folder)
    return (sub / f"{sid}.mp4", sub / f"{sid}.gif",
            sub / f"{sid}.json", sub / f"{sid}-frames")


def validate_scenario(scn) -> list:
    """Error strings; [] means the scenario is filmable.

    Checks shape (id/kind/title/beats/batch), beat types, durations,
    and the 30-60s total. Per-beat required keys are enforced per type.
    """
    errors = []
    try:
        if not isinstance(scn, dict):
            return ["scenario must be a dict"]
        for key in ("id", "kind", "title", "beats"):
            if not scn.get(key):
                errors.append(f"missing {key}")
        if scn.get("kind") not in ("improvement", "feature"):
            errors.append("kind must be improvement|feature")
        batch = scn.get("batch")
        if not isinstance(batch, int) or isinstance(batch, bool) or batch < 1:
            errors.append("batch must be a positive int")
        item = scn.get("item")
        if item is not None:
            if (not isinstance(item, str)
                    or not re.match(r"^[IF]-\d+$", item)):
                errors.append("item must look like I-N or F-N")
        beats = scn.get("beats")
        if not isinstance(beats, list) or not beats:
            return errors + ["beats must be a non-empty list"]
        for i, beat in enumerate(beats):
            where = f"beat{i}"
            if not isinstance(beat, dict):
                errors.append(f"{where}: must be a dict")
                continue
            kind = beat.get("type")
            if kind not in BEAT_TYPES:
                errors.append(f"{where}: bad type {kind!r}")
                continue
            try:
                dur = float(beat.get("duration", 0))
            except (TypeError, ValueError):
                errors.append(f"{where}: bad duration")
                continue
            if not 2 <= dur <= 20:
                errors.append(f"{where}: duration {dur} outside 2-20s")
            if kind == "title":
                if not beat.get("title"):
                    errors.append(f"{where}: title beat needs title")
            elif kind == "chrome":
                if not str(beat.get("url_path", "")).startswith("/"):
                    errors.append(f"{where}: chrome beat needs url_path")
            elif kind == "terminal":
                if not beat.get("commands"):
                    errors.append(f"{where}: terminal beat needs commands")
        total = total_duration(beats)
        if not MIN_SECONDS <= total <= MAX_SECONDS:
            errors.append(
                f"total {total:.1f}s outside {MIN_SECONDS:.0f}-{MAX_SECONDS:.0f}s")
    except Exception as exc:  # noqa: BLE001 -- validation never raises
        errors.append(f"validator error: {exc}")
    return errors


def build_concat_list(frames) -> str:
    """ffmpeg concat demuxer text for [(path, seconds)].

    Every entry carries its duration; the last file is repeated bare.
    ffmpeg's demuxer ignores the FINAL entry's own duration (it
    inherits the previous one), so the repeated tail absorbs the
    quirk and film() trims the output to the authored total with -t.
    """
    lines = []
    for path, seconds in frames or []:
        safe = str(path).replace("'", "'\\''")
        lines.append(f"file '{safe}'")
        lines.append(f"duration {float(seconds):.3f}")
    if frames:
        safe = str(frames[-1][0]).replace("'", "'\\''")
        lines.append(f"file '{safe}'")
    return "\n".join(lines) + "\n" if lines else ""


def ffmpeg_cmd(list_path, out_path, total: float,
               width=WIDTH, height=HEIGHT) -> list:
    """ffmpeg argv: stills -> padded H.264 mp4 at WIDTHxHEIGHT.

    -t trims the inherited-duration tail (see build_concat_list) so
    the mp4 lands exactly on the authored total.
    """
    vf = (f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
          f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
          f"fps={FPS},format=yuv420p")
    return ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_path), "-vf", vf,
            "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-t", f"{float(total):.3f}",
            str(out_path)]


def gif_cmd(list_path, gif_path, total: float,
            width=720, fps=8) -> list:
    """ffmpeg argv: same stills -> small README-friendly looping GIF.

    Downscaled + palette-quantized so the GIF stays embeddable in
    docs/README while the mp4 keeps full 1280x720 quality. -t trims
    the inherited-duration tail like the mp4 path.
    """
    vf = (f"fps={fps},scale={width}:-1:flags=lanczos,"
          "split[s0][s1];[s0]palettegen=max_colors=256[p];[s1][p]paletteuse")
    return ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_path), "-vf", vf, "-loop", "0",
            "-t", f"{float(total):.3f}", str(gif_path)]


def check_duration_ok(seconds) -> bool:
    """True when the finished mp4 lands inside the 30-60s window."""
    try:
        return MIN_SECONDS <= float(seconds) <= MAX_SECONDS
    except (TypeError, ValueError):
        return False


def title_html(kicker: str, title: str, subtitle: str = "") -> str:
    """Full-frame title card; screenshotted like any other beat."""
    return f"""<!doctype html><html><head><meta charset="utf-8">
<style>body{{margin:0;background:#101418;color:#f2f4f8;font:20px/1.5 system-ui,sans-serif;
display:flex;min-height:100vh;align-items:center;justify-content:center}}
.card{{max-width:820px;padding:48px;text-align:center}}
.kicker{{text-transform:uppercase;letter-spacing:3px;font-size:15px;color:#8fd0ff}}
h1{{font-size:46px;margin:14px 0}}p{{color:#c4ccd6}}</style></head><body>
<div class="card"><div class="kicker">{html.escape(kicker)}</div>
<h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div></body></html>"""


def terminal_html(caption: str, blocks) -> str:
    """Dark terminal card for [(cmd_argv, output)]; caption rides on top."""
    rows = []
    for argv, output in blocks or []:
        cmd = " ".join(str(a) for a in (argv or []))
        rows.append(f"<div class='cmd'><span>$</span> {html.escape(cmd)}</div>")
        rows.append(f"<pre>{html.escape(str(output or ''))[:3000]}</pre>")
    return f"""<!doctype html><html><head><meta charset="utf-8">
<style>body{{margin:0;background:#0b0e12;color:#e8edf3;font:19px/1.55 ui-monospace,monospace}}
.wrap{{max-width:1020px;margin:0 auto;padding:40px}}
.cap{{background:#16202c;border-left:4px solid #8fd0ff;padding:10px 14px;margin-bottom:22px;
font-family:system-ui,sans-serif}}
.cmd{{color:#8fd0ff;margin-top:14px}}.cmd span{{color:#7d8590}}
pre{{background:#11161d;padding:12px 14px;border-radius:8px;white-space:pre-wrap;margin:6px 0 0}}</style>
</head><body><div class="wrap"><div class="cap">{html.escape(caption)}</div>
{"".join(rows)}</div></body></html>"""


def frame_js(caption: str, focus: str = "") -> str:
    """JS: frame the shot as in-flow content at the top of the page.

    The caption is prepended in the normal flow (fixed overlays do
    not survive screenshots), and with ``focus`` the <main> is
    reframed to just that section (heading + body until the next
    H2/H3) — the real server HTML, cropped like a zoom. Page <style>
    lives in <head>, so reframed sections keep their styling. Ends
    with scrollTo(0,0): app scripts (verdict auto-scroll) may have
    scrolled, and the shot follows the live viewport.
    """
    cap = json.dumps(caption or "")
    target = json.dumps(focus or "")
    return (f"() => {{ const old = document.querySelector('#demo-cap'); "
            "if (old) old.remove(); const d = document.createElement('div'); "
            "d.id = 'demo-cap'; d.textContent = " + cap + "; "
            "d.setAttribute('style', 'background:#101418;color:#fff;"
            "font:18px/1.4 system-ui;padding:12px 20px;"
            "border-left:4px solid #8fd0ff;margin:0 0 12px 0'); "
            f"const t = {target}; if (!t) {{ "
            "document.body.insertBefore(d, document.body.firstChild); "
            "window.scrollTo(0,0); return 'caption-ok'; } "
            "const el = document.querySelector(t); "
            "if (!el) return 'focus-missing'; const keep = [el]; "
            "let n = el.nextElementSibling; "
            "while (n && !/^H[23]$/.test(n.tagName)) { keep.push(n); "
            "n = n.nextElementSibling; } "
            "const html = keep.map(k => k.outerHTML).join(''); "
            "const main = document.querySelector('main') || document.body; "
            "main.innerHTML = ''; main.appendChild(d); "
            "main.insertAdjacentHTML('beforeend', html); "
            "window.scrollTo(0,0); return 'framed'; }")


def render_beat(beat: dict, seed_info) -> dict:
    """Deep-copy a beat with {seed_<key>} tokens filled from seed_info."""
    try:
        text = json.dumps(beat)
    except (TypeError, ValueError):
        return beat
    for key, value in (seed_info or {}).items():
        text = text.replace("{seed_" + str(key) + "}", str(value))
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return beat


# ------------------------------------------------------------ chrome helpers

def unwrap_eval(text: str):
    m = re.search(r"```json\s*\n(.*?)```", text, re.S)
    payload = m.group(1).strip() if m else text.strip()
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return payload


def eval_js(c: MCPClient, pid: int, fn: str):
    res = c.call("evaluate_script", {"pageId": pid, "function": fn})
    return "\n".join(item.get("text", "") for item in res.get("content", [])
                     if item.get("type") == "text")


def selected_page_id(c: MCPClient) -> int:
    res = c.call("list_pages", {})
    text = "\n".join(item.get("text", "") for item in res.get("content", [])
                     if item.get("type") == "text")
    m = re.search(r"(\d+):[^\n]*\[selected\]", text)
    if not m:
        raise RuntimeError(f"no selected page in: {text[:300]}")
    return int(m.group(1))


def visit(c: MCPClient, url: str, timeout: float = 45.0) -> int:
    print(f"[demo] open {url}", flush=True)
    res = c.call("new_page", {"url": url}, timeout=60)
    if res.get("isError"):
        raise RuntimeError(f"new_page {url}: {json.dumps(res)[:300]}")
    pid = selected_page_id(c)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            state = str(unwrap_eval(
                eval_js(c, pid, "() => document.readyState"))).strip()
            href = str(unwrap_eval(
                eval_js(c, pid, "() => location.href"))).strip()
        except Exception as exc:
            print(f"[demo]   eval retry: {exc!r:.120}", flush=True)
            time.sleep(1.0)
            continue
        if state == "complete" and href.startswith(("http", "file")):
            print(f"[demo]   ready page={pid} {href[:90]}", flush=True)
            break
        time.sleep(0.5)
    else:
        raise RuntimeError(f"page never ready: {url} (page {pid})")
    res = c.call("emulate", {"pageId": pid, "viewport": VIEWPORT},
                 timeout=60)
    if res.get("isError"):
        raise RuntimeError(f"viewport {VIEWPORT}: {json.dumps(res)[:200]}")
    time.sleep(0.5)
    return pid


def screenshot(c: MCPClient, pid: int, path: Path) -> None:
    res = c.call("take_screenshot",
                 {"pageId": pid, "format": "png",
                  "filePath": str(path)}, timeout=60)
    if res.get("isError") or not path.exists():
        raise RuntimeError(f"screenshot: {json.dumps(res)[:300]}")


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


# -------------------------------------------------------------- beat runners

def run_title_beat(c: MCPClient, beat: dict, shot: Path,
                   work: Path, index: int) -> None:
    page = work / f"title{index}.html"
    page.write_text(title_html(beat.get("kicker", "Groundwork demo"),
                               beat.get("title", ""),
                               beat.get("subtitle", "")))
    pid = visit(c, page.as_uri())
    time.sleep(0.8)
    screenshot(c, pid, shot)


def run_chrome_beat(c: MCPClient, beat: dict, shot: Path, base: str) -> dict:
    """Navigate, interact, wait, frame caption/focus, assert, screenshot.

    Framing runs AFTER any navigation the js/poll caused (a submit
    lands on a new page); poll_required beats fail loudly instead of
    filming the wrong screen.
    """
    pid = visit(c, base + beat["url_path"])
    for fn in beat.get("js", []) or []:
        unwrap_eval(eval_js(c, pid, fn))
        time.sleep(0.4)
    if beat.get("poll_js"):
        deadline = time.time() + float(beat.get("poll_timeout", 25))
        seen = ""
        found = False
        while time.time() < deadline:
            time.sleep(1.0)
            try:
                state = str(unwrap_eval(eval_js(
                    c, pid, "() => document.readyState"))).strip()
                if state != "complete":
                    continue
                seen = str(unwrap_eval(eval_js(c, pid, beat["poll_js"])))
            except Exception:
                continue
            if beat.get("poll_want", "") in seen:
                found = True
                break
        if not found and beat.get("poll_required"):
            raise RuntimeError(
                f"beat poll failed: {beat.get('poll_want')!r} not seen; "
                f"last body head: {seen[:200]!r}")
    caption = beat.get("caption", "")
    focus = beat.get("focus", beat.get("scroll_to", ""))
    if caption or focus:
        framed = unwrap_eval(eval_js(c, pid, frame_js(caption, focus)))
        if focus and str(framed) != "framed":
            raise RuntimeError(f"beat focus failed: {focus!r} ({framed})")
        time.sleep(0.8)
    detail = ""
    if beat.get("assert_js"):
        val = str(unwrap_eval(eval_js(c, pid, beat["assert_js"])))
        want = beat.get("assert_want", "")
        if want not in val:
            raise RuntimeError(f"beat assert failed: want {want!r} in {val[:200]!r}")
        detail = val[:200]
    screenshot(c, pid, shot)
    return {"detail": detail}


def run_terminal_beat(c: MCPClient, beat: dict, shot: Path,
                      work: Path, index: int) -> None:
    blocks = []
    env = {**os.environ,
           "DEMO_DB": os.environ.get("DEMO_DB", str(ROOT / "groundwork.db"))}
    for cmd in beat.get("commands", []):
        argv = cmd if isinstance(cmd, list) else ["bash", "-lc", str(cmd)]
        proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                              timeout=60, env=env)
        output = (proc.stdout or "") + (proc.stderr or "")
        blocks.append((argv, output.strip() or "(no output)"))
    page = work / f"term{index}.html"
    page.write_text(terminal_html(beat.get("caption", "Terminal"), blocks))
    pid = visit(c, page.as_uri())
    time.sleep(0.8)
    screenshot(c, pid, shot)


# ----------------------------------------------------------------- assembly

def list_scenarios() -> list:
    out = []
    demos = ROOT / "tools" / "demos"
    if demos.is_dir():
        for mod in sorted(demos.glob("*.py")):
            if mod.name.startswith("_"):
                continue
            out.append(mod.stem)
    return out


def load_scenario(name: str):
    try:
        module = importlib.import_module(f"tools.demos.{name}")
    except ImportError:
        module = importlib.import_module(f"demos.{name}")
    scn = module.SCENARIO
    errors = validate_scenario(scn)
    if errors:
        raise SystemExit(f"scenario {name} invalid: {'; '.join(errors)}")
    seed = getattr(module, "seed_db", None)
    return scn, seed


def probe_duration(path: Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=30)
    return float((proc.stdout or "").strip())


def film(scn: dict, seed, out_dir: Path, keep: bool, port: int,
         want_gif: bool = True) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="demovid"))
    frames = tmp / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    db = tmp / "demo.db"
    shutil.copy(ROOT / "groundwork.db", db)
    os.environ["DEMO_DB"] = str(db)
    seed_info = seed(str(db)) if seed else {}
    if seed_info:
        print(f"[demo] seed: {json.dumps(seed_info)[:300]}", flush=True)

    server = subprocess.Popen(
        [sys.executable, "-m", "groundwork", "--db", str(db),
         "serve", "--port", str(port)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    base = f"http://127.0.0.1:{port}"
    out_path, gif_path, json_path, keep_dir = output_paths(out_dir, scn)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        wait_for_server(base)
        client = MCPClient(roots=[str(frames), str(tmp)],
                           screenshot_max_width=SHOT_WIDTH)
        shots: list = []
        try:
            for i, beat in enumerate(scn["beats"]):
                beat = render_beat(beat, seed_info)
                # .png: lossless intermediates; the server honors the
                # per-call format (its jpeg default is for the sweep).
                shot = frames / f"beat{i:02d}.png"
                kind = beat["type"]
                print(f"[demo] beat{i} {kind} {beat.get('duration')}s",
                      flush=True)
                if kind == "title":
                    run_title_beat(client, beat, shot, tmp, i)
                elif kind == "chrome":
                    run_chrome_beat(client, beat, shot, base)
                else:
                    run_terminal_beat(client, beat, shot, tmp, i)
                shots.append((shot, float(beat["duration"])))
        finally:
            client.close()
        authored = total_duration(scn["beats"])
        list_path = tmp / "concat.txt"
        list_path.write_text(build_concat_list(shots))
        cmd = ffmpeg_cmd(list_path, out_path, authored)
        print(f"[demo] assemble: {' '.join(cmd)[:200]}", flush=True)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0 or not out_path.exists():
            raise RuntimeError(f"ffmpeg failed: {(proc.stderr or '')[-1500:]}")
        seconds = probe_duration(out_path)
        print(f"[demo] wrote {out_path} {seconds:.1f}s", flush=True)
        if not check_duration_ok(seconds):
            raise RuntimeError(
                f"{out_path.name} is {seconds:.1f}s, need 30-60s")
        gif_bytes = 0
        if want_gif:
            gcmd = gif_cmd(list_path, gif_path, authored)
            gproc = subprocess.run(gcmd, capture_output=True, text=True,
                                   timeout=300)
            if gproc.returncode != 0 or not gif_path.exists():
                raise RuntimeError(
                    f"gif failed: {(gproc.stderr or '')[-1200:]}")
            gif_bytes = gif_path.stat().st_size
            print(f"[demo] wrote {gif_path} {gif_bytes / 1e6:.1f}MB",
                  flush=True)
            if gif_bytes > 10 * 1024 * 1024:
                print("[demo] WARNING: gif over 10MB; prefer a shorter "
                      "cut for README embeds", flush=True)
        manifest = {"scenario": scn["id"], "kind": scn.get("kind"),
                    "batch": scn.get("batch"), "item": scn.get("item"),
                    "title": scn.get("title"), "seconds": seconds,
                    "beats": len(shots), "seed": seed_info,
                    "output": str(out_path),
                    "gif": str(gif_path) if want_gif else "",
                    "gif_bytes": gif_bytes}
        json_path.write_text(json.dumps(manifest, indent=1))
        if keep:
            shutil.rmtree(keep_dir, ignore_errors=True)
            shutil.copytree(frames, keep_dir)
        return out_path
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except Exception:
            server.kill()
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            print(f"[demo] work kept at {tmp}", flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default=None)
    ap.add_argument("--out", default="demos")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--port", type=int, default=8767)
    ap.add_argument("--no-gif", action="store_true",
                    help="skip the README-sized gif; mp4 only")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    if args.list or not args.scenario:
        print("\n".join(list_scenarios()) or "(no scenarios in tools/demos/)")
        return 0
    scn, seed = load_scenario(args.scenario)
    film(scn, seed, Path(args.out), args.keep, args.port,
         want_gif=not args.no_gif)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
