"""Logging retrofit: add observability at the right lines (F-7).

Exercise type 29 ("logging-retrofit", bloom "analyse"). The learner gets
a plain snippet with no logging and a short checklist of the lines that
deserve a log call; for each marked line they name the level
(debug/info/warning/error). Grading is a pure checklist compare — every
item must match, with partial credit — so no sandbox runner is needed.

Level key (also stated in the prompt): function entry/exit is debug,
a caught problem (except) is warning, a raised failure is error.

Pure functions, stdlib only, no groundwork imports: this module is
import-safe standalone. Registration lives in groundwork/exercises.py
(TYPES/GENERATORS/BLOOM_TYPES plus thin gen_logretro/grade branches).
"""
from __future__ import annotations

import html
import re

TYPE_NUM = 29
TYPE_NAME = "logging-retrofit"
BLOOM = "analyse"

LEVELS = ("debug", "info", "warning", "error")

_ALIASES = {
    "dbg": "debug",
    "information": "info", "informational": "info",
    "warn": "warning",
    "err": "error", "errored": "error", "exception": "error",
    "critical": "error", "fatal": "error",
}

_KIND_LEVEL = {
    "entry": "debug",
    "exit": "debug",
    "except": "warning",
    "raise": "error",
}

_KIND_WHY = {
    "entry": "function entry traces at debug",
    "exit": "return value traces at debug",
    "except": "a caught problem warns",
    "raise": "a raised failure errors",
}

_PATTERNS = (
    ("entry", re.compile(r"^\s*(?:async\s+)?def\s+[A-Za-z_]\w*")),
    ("raise", re.compile(r"^\s*raise\b")),
    ("except", re.compile(r"^\s*except\b")),
    ("exit", re.compile(r"^\s*(?:return|yield)\b")),
)

_MAX_ITEMS = 4


def _classify(line: str) -> str | None:
    """Observability kind of one source line, or None."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    for kind, rx in _PATTERNS:
        if rx.search(line):
            return kind
    return None


def pick_lines(snippet: list[str]) -> list[dict]:
    """Checklist candidates: first _MAX_ITEMS classifiable lines, in order."""
    items = []
    for n, line in enumerate(list(snippet or [])):
        kind = _classify(line)
        if kind is None:
            continue
        items.append({"id": len(items), "line": n + 1, "kind": kind,
                      "level": _KIND_LEVEL[kind], "text": line.strip(),
                      "why": _KIND_WHY[kind]})
        if len(items) >= _MAX_ITEMS:
            break
    return items


def _fallback_item(concept) -> list[dict]:
    name = getattr(concept, "name", "concept")
    return [{"id": 0, "line": getattr(concept, "line", 1) or 1,
             "kind": "entry", "level": "debug",
             "text": f"def {name}(...)",
             "why": _KIND_WHY["entry"]}]


def _hints(concept, snippet, first: dict) -> list[str]:
    where = f"{concept.file}:{concept.line}" if getattr(concept, "line", 0) else getattr(concept, "file", "")
    pointer = f"Look at {where}: `{snippet[0].strip()}`" if snippet and where else "Re-read the snippet."
    return [f"Match each marked line to its moment: entry/exit is debug, "
            f"a caught problem is warning, a raised failure is error.",
            pointer,
            f"Worked step: line {first['line']} ({first['kind']}) "
            f"takes `{first['level']}`. Now place the rest."]


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build the type-29 exercise dict (same keys as exercises._base)."""
    snippet = list(snippet or [])
    ctx = ctx or {}
    items = pick_lines(snippet) or _fallback_item(concept)
    grounded = bool(pick_lines(snippet))
    first = items[0]
    numbered = []
    marked = {it["line"] for it in items}
    by_line = {it["line"]: it["id"] for it in items}
    for n, line in enumerate(snippet, 1):
        tag = f"  # (item {by_line[n]})" if n in marked else ""
        numbered.append(f"{n}: {line}{tag}")
    code = "\n".join(numbered) if numbered else first["text"]
    want = "\n".join(f"{it['id']}={it['level']}" for it in items)
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM,
        "concept_id": getattr(concept, "node_id", ""),
        "concept": getattr(concept, "name", ""),
        "file": getattr(concept, "file", ""),
        "line": getattr(concept, "line", 0),
        "commit": ctx.get("commit", ""),
        "hints": _hints(concept, snippet, first),
        "front": ("Add logging at the right lines: reply `id=level` "
                  "(one per line) using debug/info/warning/error.\n"
                  f"```\n{code[:800]}\n```"),
        "back": want,
        "payload": {"checklist": [
            {"id": it["id"], "line": it["line"], "kind": it["kind"],
             "level": it["level"]} for it in items],
            "levels": list(LEVELS), "grounded": grounded},
    }


def _norm_level(raw: str) -> str:
    word = raw.strip().lower()
    return _ALIASES.get(word, word)


def _parse_items(submission: str) -> dict:
    """Parse `id=level` pairs; also accepts comma/semicolon separation."""
    out: dict = {}
    text = str(submission).replace(",", "\n").replace(";", "\n")
    for chunk in text.splitlines():
        if "=" not in chunk:
            continue
        k, v = chunk.split("=", 1)
        k, v = k.strip(), v.strip()
        if not v:
            continue
        try:
            out[int(k)] = _norm_level(v)
        except ValueError:
            continue
    return out


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Grade the checklist: all levels right passes, partial credit else."""
    items = (exercise.get("payload", {}) or {}).get("checklist", [])
    if not items:
        return {"pass": False, "score": 0.0,
                "feedback": "No checklist to grade."}
    if len(items) == 1 and "=" not in str(submission):
        given = {items[0]["id"]: _norm_level(str(submission))}
    else:
        given = _parse_items(submission)
    if not given:
        return {"pass": False, "score": 0.0,
                "feedback": "Reply `id=level` per marked line "
                "(levels: debug/info/warning/error)."}
    wrong = [str(it["id"]) for it in items
             if given.get(it["id"], "") != it["level"]]
    unknown = sorted({v for v in given.values() if v not in LEVELS})
    ok = not wrong
    score = (len(items) - len(wrong)) / len(items)
    if ok:
        return {"pass": True, "score": 1.0,
                "feedback": "Every line logged at the right level."}
    detail = f"Item(s) {', '.join(wrong)} wrong ({len(items) - len(wrong)}/{len(items)} right)."
    if unknown:
        detail += f" Unknown level(s): {', '.join(unknown)}."
    return {"pass": False, "score": score, "feedback": detail}


def render(exercise: dict) -> str:
    """Article HTML: numbered snippet, level textarea, hints, file footer."""
    p = exercise.get("payload", {}) or {}
    items = p.get("checklist", [])
    front = html.escape(exercise.get("front", ""))
    rows = "".join(
        f"<li>line {it['line']} <small>({html.escape(it['kind'])})</small> "
        f"<input name='lv{it['id']}' size='8' placeholder='level'></li>"
        for it in items)
    return (
        f"<article><h3>{html.escape(exercise.get('concept', ''))} "
        f"· {html.escape(exercise.get('type_name', TYPE_NAME))}</h3>"
        f"<p>{front}</p>"
        f"<p><small>Levels: {', '.join(p.get('levels', list(LEVELS)))}. "
        f"Example answer: <code>0=debug</code>.</small></p>"
        f"<form method='post'><textarea name='answer' rows='6' cols='40' "
        f"placeholder='0=debug'>"
        f"</textarea><br><button>Submit</button></form>"
        f"<ol>{rows}</ol>"
        + "".join(f"<details><summary>Hint {i + 1}</summary>"
                  f"{html.escape(h)}</details>"
                  for i, h in enumerate(exercise.get("hints", [])))
        + f"<p><small>{html.escape(exercise.get('file', ''))}:"
        f"{exercise.get('line', 0)}</small></p></article>")


def section_html(db_path: str = "") -> str:
    """Status-page home for this item (no DB needed; db_path matches siblings)."""
    return ("<h2 id='status-b6-logretro'>Logging retrofit</h2>"
            "<p>Type 29 exercise (<code>groundwork/logretro.py</code>): the learner "
            "adds log calls at the right lines — entry/exit at debug, caught "
            "problems at warning, raised failures at error — and names each level. "
            "Checklist-graded, no sandbox; at most 4 marked lines per card.</p>")
