"""Pre-mortem exercise (type 78, F-74, bloom: evaluate).

List how this code could fail before it does: the learner writes the
failure modes of a function (unhandled errors, missing retries, races,
leaks, silent data loss) against a statically derived checklist (ast +
line scans; deterministic, sandbox-free). No analysable failure surface
yields an ungrounded card the pipeline drops -- never None
(all-types-generate contract holds). Never raises. Registered in
``groundwork/exercises.py``.
"""
from __future__ import annotations

import ast
import html
import re

TYPE_NUM = 78
TYPE_NAME = "pre-mortem"
BLOOM = "evaluate"
STATUS_ANCHOR = "status-b18-premortem"

CODE_LIMIT = 800
MAX_ITEMS = 6  # checklist stays reviewable; detectors run in fixed order

# Detector = (item_id, label, key phrases for tolerant matching).
# Order is the presentation order (fixed => deterministic).
DETECTORS = (
    ("unhandled-error", "Unhandled error: exception path escapes with no try/except",
     ("unhandled", "exception", "try", "except")),
    ("broad-except", "Overbroad except hides the failure instead of handling it",
     ("broad except", "bare except", "swallow")),
    ("no-retry", "No retry/timeout around a fallible call (network, subprocess, IO)",
     ("retry", "timeout", "backoff")),
    ("race", "Shared-state race: threads, locks, or read-modify-write with no guard",
     ("race", "thread", "lock", "concurrent")),
    ("resource-leak", "Resource leak: open()/lock acquired with no close/release path",
     ("leak", "close", "release", "open(")),
    ("silent-loss", "Silent data loss: failure returns empty/default with no signal",
     ("data loss", "silent", "empty", "default")),
    ("boundary", "Boundary slip: off-by-one, empty input, or unguarded index/slice",
     ("boundary", "off-by-one", "empty", "index")),
    ("stale-state", "Stale state: cache/backfill read with no invalidation or refresh",
     ("stale", "cache", "invalidat", "refresh")),
    ("double-run", "Double-run hazard: re-execution duplicates a side effect",
     ("idempot", "double", "duplicate", "side effect")),
    ("hardcoded-assumption", "Hardcoded assumption: literal path, count, or constant that breaks elsewhere",
     ("hardcod", "assumption", "literal", "constant")),
)

_NETISH = {"get", "post", "put", "request", "urlopen", "urlretrieve", "fetch"}
_FALLIBLE = {"get", "post", "put", "request", "urlopen", "run", "call",
             "Popen", "read", "write", "open", "connect", "fetch"}


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _code_of(snippet) -> str:
    if isinstance(snippet, str):
        return snippet
    try:
        return "\n".join(str(l) for l in (snippet or []))
    except TypeError:
        return ""


def _tree(code: str):
    try:
        return ast.parse(code)
    except (SyntaxError, ValueError):
        return None


def _call_names(tree) -> list[str]:
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Name):
            out.append(f.id)
        elif isinstance(f, ast.Attribute):
            out.append(f.attr)
    return out


def _detect_from_tree(code: str, tree) -> list[str]:
    found: list[str] = []

    def add(item: str) -> None:
        if item not in found:
            found.append(item)

    calls = _call_names(tree)
    names = {c.split(".")[-1] for c in calls}
    handlers = [h for h in ast.walk(tree)
                if isinstance(h, ast.ExceptHandler)]
    has_try = any(isinstance(n, ast.Try) for n in ast.walk(tree))
    if not has_try and ("raise" in code or names & {"open", "read", "write",
            "connect", "get", "post", "run", "execute"}):
        add("unhandled-error")
    if any(h.type is None or (isinstance(h.type, ast.Name)
            and h.type.id in ("Exception", "BaseException"))
           for h in handlers):
        add("broad-except")
    if names & _FALLIBLE and not any(
            t in code for t in ("retry", "Retry", "timeout", "Timeout",
                                "backoff", "attempt")):
        add("no-retry")
    if any(t in code for t in ("Thread", "threading", "Lock", "asyncio",
                               "global ")) and not any(
            t in code for t in ("Lock", "lock", "copy", "queue")):
        add("race")
    if "open(" in code and "close()" not in code and "with " not in code:
        add("resource-leak")
    if re.search(r"except\s*:|except\s+Exception[\s:]", code) and \
            re.search(r"return\s+(\[\]|{}|\"\"|None|0)\s*$", code, re.M):
        add("silent-loss")
    if any(t in code for t in ("[0]", "[-1]", "range(len", "len(")) and \
            "if not" not in code and "assert" not in code:
        add("boundary")
    if any(t.lower() in code.lower() for t in ("cache", "backfill")) and not any(
            t.lower() in code.lower() for t in ("invalidat", "refresh", "ttl", "expire")):
        add("stale-state")
    if any(t in code for t in ("insert", "send", "charge", "append", "write")) \
            and not any(t.lower() in code.lower()
                        for t in ("idempot", "dedup", "once", "exists")):
        add("double-run")
    if re.search(r"(?i)\b(path|count|limit|retries)\s*=\s*['\"]?[/\w.]+", code) \
            and "environ" not in code and "config" not in code.lower():
        add("hardcoded-assumption")
    order = [d[0] for d in DETECTORS]
    return sorted(found, key=order.index)[:MAX_ITEMS]


def _detect_from_text(code: str) -> list[str]:
    low = code.lower()
    hits: list[str] = []

    def add(item: str, cond: bool) -> None:
        if cond and item not in hits:
            hits.append(item)

    add("unhandled-error", "raise" in low and "try" not in low)
    add("broad-except", bool(re.search(r"except\s*:|except\s+Exception", code)))
    add("no-retry", ("requests" in low or "subprocess" in low) and "retry" not in low)
    add("race", "thread" in low and "lock" not in low)
    add("resource-leak", "open(" in low and "close()" not in low and "with " not in low)
    add("silent-loss", "except" in low and "return []" in low)
    add("boundary", "len(" in low and "if not" not in low)
    add("stale-state", "cache" in low and "invalidat" not in low)
    add("double-run", "insert" in low and "idempot" not in low)
    add("hardcoded-assumption", "path = " in low and "environ" not in low)
    order = [d[0] for d in DETECTORS]
    return sorted(hits, key=order.index)[:MAX_ITEMS]


def _labels(ids: list[str]) -> list[str]:
    by_id = {d[0]: d[1] for d in DETECTORS}
    return [by_id[i] for i in ids if i in by_id]


def _keys(ids: list[str]) -> list[list[str]]:
    by_id = {d[0]: list(d[2]) for d in DETECTORS}
    return [by_id[i] for i in ids if i in by_id]


def _empty_card(ex_id, name, file, line, commit, code):
    front = (f"Pre-mortem `{name}`: list how this code could fail, one per line.\n"
             f"```python\n{code[:CODE_LIMIT]}\n```\n"
             "No failure surface found here -- this card is skipped.")
    return {"id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": name, "concept": name,
            "file": file, "line": line, "commit": commit,
            "hints": ["No fallible calls, shared state, or literals: nothing to list."],
            "front": front, "back": "No failure surface found.",
            "payload": {"items": [], "grounded": False,
                        "check": "pre-mortem", "solution": []}}


def generate(ex_id, concept, snippet, ctx):
    """Build a pre-mortem checklist card (never raises, never None)."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        name = _concept_field(concept, "name", "function") or "function"
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        code = _code_of(snippet)[:4000]
        if not code.strip():
            return _empty_card(ex_id, name, file, line, commit, code)
        tree = _tree(code)
        ids = (_detect_from_tree(code, tree) if tree is not None
               else _detect_from_text(code))
        if not ids:
            return _empty_card(ex_id, name, file, line, commit, code)
        items = _labels(ids)
        front = (f"Pre-mortem `{name}`: assume it failed in production. "
                 f"List how ({len(items)} failure modes, one per line).\n"
                 f"```python\n{code[:CODE_LIMIT]}\n```")
        back = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(items))
        hints = [
            "Follow each fallible call: what if it raises, times out, or never answers?",
            "Run it twice in your head: what duplicates, leaks, or goes stale?",
            "Empty input, first/last element, hardcoded paths -- boundaries and assumptions count.",
        ]
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": hints, "front": front, "back": back,
            "payload": {"items": items, "keys": _keys(ids),
                        "solution": items, "surface": ids,
                        "check": "pre-mortem", "grounded": True},
        }
    except Exception:  # never raise, never None: ungrounded card
        return _empty_card(ex_id, "function", "", 0, "", "")


gen_premortem = generate  # card-type alias: gen_<name>(ex_id, concept, snippet, ctx)->dict


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _fold(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", str(text).lower())


def _tokens(text: str) -> set[str]:
    return {w for w in _fold(text).split() if len(w) > 2}


def _hit(label: str, keys: list[str], blob: str, toks: set[str]) -> bool:
    folded = _fold(label)
    if folded and folded in blob:
        return True
    if any(k and _fold(k) in blob for k in keys):
        return True
    lt = _tokens(label)
    if lt and len(lt & toks) / len(lt) >= 0.5:
        return True
    return False


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Checklist match: partial credit per item, fail closed. Never raises."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {})
        items = list(payload.get("items", []) or [])
        keys = list(payload.get("keys", []) or [])
        if not items:
            return _fail("Exercise payload is missing the checklist.")
        text = str(submission if submission is not None else "").strip()
        if not text:
            return _fail("List at least one failure mode, one per line "
                         f"(this code has {len(items)}).")
        blob = _fold(text)
        toks = _tokens(text)
        missed: list[str] = []
        for i, label in enumerate(items):
            ks = list(keys[i]) if i < len(keys) and keys[i] else []
            if not _hit(str(label), [str(k) for k in ks], blob, toks):
                missed.append(str(label))
        got = len(items) - len(missed)
        score = got / len(items)
        if got == len(items):
            return {"pass": True, "score": 1.0,
                    "feedback": f"Full pre-mortem ({got}/{len(items)} modes)."}
        ok = score >= 0.5
        detail = (f"Matched {got}/{len(items)} modes."
                  + ("" if ok else " Need at least half to pass.")
                  + f" Missing: {'; '.join(missed)[:200]}")
        return {"pass": ok, "score": score, "feedback": detail}
    except Exception:  # noqa: BLE001 -- grading must never raise
        return _fail("Grader could not read the submission -- list failure modes, one per line.")


def render(exercise: dict) -> str:
    """Function code + failure-mode textarea widget (threatmodel shape)."""
    payload = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    n = len(payload.get("items", []))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Checklist match -- name at least half of the "
        f"{n} failure modes (spelling/punctuation-folded, partial credit "
        f"per item). No sandbox.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='6' cols='70' "
        f"placeholder='One failure mode per line ({n} to find)'></textarea><br>"
        f"<button>Check pre-mortem</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch18.py."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Pre-mortem <small>(feature)</small></h3>"
        "<p>Assume the code already failed in production and list how -- "
        "unhandled errors, missing retries, races, leaks, silent loss -- "
        "graded against a statically derived checklist with per-item "
        "partial credit, no sandbox. "
        "<code>groundwork/premortem.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "pre-mortem", "kind": "feature",
            "title": "Pre-mortem",
            "blurb": "List how this code could fail before it does -- errors, retries, races, leaks.",
            "path": "/status", "anchor": "status-b18-premortem"}
