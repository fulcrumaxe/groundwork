"""Memory-profile reading (F-13, type 36, bloom: analyse).

The learner reads a small deterministic tracemalloc-style snapshot built
from the snippet's own lines and names the top-allocating line. The
snapshot is fabricated at generation time from line content with a
stable-seeded RNG (never measured live), so cards are stable and
flake-free, yet self-consistent: the shown rows always rank the payload
answer first. Grading is an exact normalized match on the line reference.

Plugin API: generate(ex_id, concept, snippet, ctx),
render(exercise) -> html, grade(exercise, submission, runner).
Import-safe standalone: stdlib only (html/random/re/zlib), no groundwork
imports. Registration lives in groundwork/exercises.py
(TYPES, GENERATORS, BLOOM_TYPES); see ===WIRES===.
"""
from __future__ import annotations

import html
import random
import re
import zlib

TYPE_NUM = 36
TYPE_NAME = "memory-profile"
BLOOM = "analyse"

_HEAVY_HINTS = ("list", "dict", "set", "append", "extend", "join",
                "read", "load", "*", "range(", "comprehension",
                "for ", "while ", "copy", "deepcopy", "bytes",
                "bytearray", "numpy", "pandas", "image", "buffer")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _weight(line: str) -> float:
    low = line.lower()
    w = 1.0 + min(len(line.strip()) / 40.0, 2.0)
    for hint in _HEAVY_HINTS:
        if hint in low:
            w += 1.5
            break
    if re.search(r"\b(def|class|import|from|pass|return\s*$)", line.strip()):
        w *= 0.2
    return max(w, 0.1)


def _frames(ex_id: str, file: str, func: str,
            snippet: list[str]) -> list[dict]:
    # Stable seed: builtin hash() is salted per process, so crc32 keeps
    # the same card identical across runs.
    seed = zlib.crc32(f"memprofile:{ex_id}".encode("utf-8"))
    rng = random.Random(seed)
    rows = []
    for i, line in enumerate(snippet):
        if not line.strip():
            continue
        rows.append((i + 1, line.strip()))
        if len(rows) >= 6:
            break
    if not rows:
        rows = [(1, "pass")]
    out = []
    for lineno, text in rows:
        jitter = 0.7 + rng.random() * 0.6
        kb = round(_weight(text) * jitter * 64.0, 1)
        count = 1 + int(kb // 32) + rng.randrange(0, 3)
        out.append({"frame": f"{file}:{lineno} ({func})",
                    "line": lineno, "func": func,
                    "code": text[:80], "kb": kb, "count": count})
    out.sort(key=lambda r: (-r["kb"], r["line"]))
    # Force a strict top: daylight between rank 1 and rank 2.
    if len(out) > 1 and out[0]["kb"] <= out[1]["kb"]:
        out[0]["kb"] = round(out[1]["kb"] + 12.5, 1)
    return out


def _answer_of(top: dict, file: str) -> str:
    return f"{file}:{top['line']}"


def _snapshot_text(snapshot: list[dict]) -> str:
    lines = ["Traceback-free snapshot (top 6 lines by allocated KiB):"]
    for r in snapshot:
        lines.append(
            f"  {r['frame']}: {r['kb']} KiB ({r['count']} blocks) | {r['code']}")
    return "\n".join(lines)


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a memory-profile reading card over the snippet's lines."""
    ctx = ctx or {}
    snippet = list(snippet or [])
    name = _concept_field(concept, "name", "func") or "func"
    file = _concept_field(concept, "file", "snippet.py") or "snippet.py"
    try:
        line = int(getattr(concept, "line", 0) or 0)
    except (TypeError, ValueError):
        line = 0
    code = str(ctx.get("runnable") or "\n".join(snippet) or "pass")
    if not snippet:
        snippet = code.splitlines() or ["pass"]
    snapshot = _frames(ex_id, file, name, snippet)
    top = snapshot[0]
    answer = _answer_of(top, file)
    shot = _snapshot_text(snapshot)
    front = (
        f"Read this tracemalloc-style snapshot for `{name}` and name the "
        f"top-allocating line (reply `file:line`):\n"
        f"```\n{shot[:900]}\n```"
    )
    back = f"{answer} ({top['func']}) allocates the most ({top['kb']} KiB)."
    where = f"{file}:{line}" if file and line else file
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM,
        "concept_id": _concept_field(concept, "node_id", name),
        "concept": name, "file": file, "line": line,
        "commit": str(ctx.get("commit", "") or ""),
        "hints": [
            f"Rank the snapshot rows by the KiB column, biggest first.",
            f"Re-check against {where}: the top frame's code should look allocation-heavy.",
            f"Worked step: the top row `{answer}` out-allocates every other row. Reply exactly that.",
        ],
        "front": front, "back": back,
        "payload": {"snapshot": snapshot, "answer": answer,
                    "top_lineno": top["line"], "top_func": top["func"],
                    "code": code[:600], "grounded": True},
    }


def _normalize(ref: str) -> str:
    text = str(ref or "").strip().lower()
    text = text.strip("`'\"")
    text = re.sub(r"\s+", "", text)
    text = text.replace("line", "")
    text = text.lstrip(":")
    return text


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Exact normalized match on the top-allocating line reference."""
    _ = runner  # reading card: no sandbox needed.
    try:
        p = (exercise or {}).get("payload", {}) if isinstance(exercise, dict) else {}
        want = _normalize(p.get("answer", ""))
        got_raw = str(submission or "").strip()
        if not got_raw:
            return _fail("Reply with the top line as `file:line`.")
        got = _normalize(got_raw)
        # Bare line number counts iff it is the top line number.
        bare = re.fullmatch(r"\d+", got)
        if bare and isinstance(p.get("top_lineno"), int):
            try:
                want_line = int(str(want).rsplit(":", 1)[-1])
            except ValueError:
                want_line = -1
            ok = int(bare.group(0)) == want_line == int(p["top_lineno"])
            return {"pass": ok, "score": 1.0 if ok else 0.0,
                    "feedback": "Top allocator found." if ok else
                    f"Not the top row — re-rank by KiB. Expected {p.get('answer')}."}
        ok = bool(want) and got == want
        return {"pass": ok, "score": 1.0 if ok else 0.0,
                "feedback": "Top allocator found." if ok else
                f"Not the top row — re-rank by KiB. Expected {p.get('answer')}."}
    except Exception:
        return _fail("Reply with the top line as `file:line`.")


def render(exercise: dict) -> str:
    """Card HTML: snapshot table plus a file:line answer box."""
    try:
        p = (exercise or {}).get("payload", {})
        front = html.escape(str(exercise.get("front", "")))
        concept = html.escape(str(exercise.get("concept", "")))
        type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
        rows = "".join(
            f"<tr><td>{html.escape(str(r.get('frame', '')))}</td>"
            f"<td>{html.escape(str(r.get('kb', '')))}</td>"
            f"<td>{html.escape(str(r.get('count', '')))}</td>"
            f"<td><code>{html.escape(str(r.get('code', '')))}</code></td></tr>"
            for r in p.get("snapshot", []))
        table = (f"<table><tr><th>Frame</th><th>KiB</th>"
                 f"<th>Blocks</th><th>Line</th></tr>{rows}</table>")
        hints = "".join(
            f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
            for i, h in enumerate(exercise.get("hints", [])))
        file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
        return (
            f"<article><h3>{concept} · {type_name}</h3>"
            f"<p>{front}</p>{table}"
            f"<form method='post'><input name='answer' size='30' "
            f"placeholder='file:line'><button>Submit</button></form>{hints}"
            f"<p><small>{html.escape(file_line)}</small></p></article>")
    except Exception:
        return "<article><p>Memory-profile card unavailable.</p></article>"


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b7-memprofile'>Memory-profile reading <small>(feature)</small></h3>"
        "<p>Read a deterministic tracemalloc-style snapshot and name the "
        "top-allocating line — exact <code>file:line</code> match, no sandbox. "
        "<code>groundwork/memprofile.py</code>.</p>"
    )
