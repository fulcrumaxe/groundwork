"""Race-hunt: spot the shared-state bug (type 37, F-14).

Name the line touching shared mutable state (module global, shared
cache, mutable class attribute) and propose the fix (local copy, lock,
or parameter). Line match plus fix-keyword checklist; no threads ever
spawned, no sandbox needed. Stdlib only, no groundwork imports.
"""
from __future__ import annotations

import ast
import html
import re

TYPE_NUM = 37
TYPE_NAME = "race-hunt"
BLOOM = "analyse"
AREA = "racehunt"

CODE_LIMIT = 800

FIX_KEYWORDS = ("copy", "deepcopy", "local", "lock", "parameter",
                "argument", "inject", "immutable", "tuple", "frozen")

_OR_LOCK_PARAM = "(or guard it with a lock, or pass it as a parameter)"

FIX_BY_KIND = {
    "module-global": f"copy it into a local {_OR_LOCK_PARAM}",
    "shared-cache": f"copy the entry into a local {_OR_LOCK_PARAM}",
    "class-attribute": f"copy it into a local {_OR_LOCK_PARAM}",
    "mutable-default": "default to None and build a fresh object inside "
                       "(or pass it as a parameter)",
}

MUTATING_METHODS = {"append", "extend", "insert", "add", "update", "pop",
                    "clear", "setdefault", "discard", "remove"}

FALLBACK_CODE = ("seen = []\n\ndef record(x):\n    global seen\n"
                 "    seen.append(x)\n    return len(seen)")

_GLOBAL_RE = re.compile(r"^\s*global\s+(.+?)\s*(?:#.*)?$")


def _tree(code: str):
    try:
        return ast.parse(code or "")
    except (SyntaxError, ValueError):
        return None


def _is_mutable_value(node) -> bool:
    if isinstance(node, (ast.List, ast.Dict, ast.Set)):
        return True
    if isinstance(node, ast.Call):
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
        return name in ("list", "dict", "set")
    return False


def _ast_sites(tree) -> list[dict]:
    """Shared-state sites ordered by line; empty when none found."""
    found: list[dict] = []
    if tree is None:
        return found
    module_mutables: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if _is_mutable_value(node.value):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        module_mutables.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None and _is_mutable_value(node.value):
                module_mutables.add(node.target.id)
    class_mutables: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and _is_mutable_value(stmt.value):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            class_mutables.add((node.name, target.id))
    default_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            pos_defaults = list(node.args.defaults)
            pos_args = list(node.args.args)
            for arg, default in zip(pos_args[len(pos_args) - len(pos_defaults):],
                                    pos_defaults):
                if _is_mutable_value(default):
                    default_names.add(arg.arg)
                    found.append({"line": node.lineno, "symbol": arg.arg,
                                  "kind": "mutable-default"})
            for arg, default in zip(node.args.kwonlyargs,
                                    node.args.kw_defaults or []):
                if default is not None and _is_mutable_value(default):
                    default_names.add(arg.arg)
                    found.append({"line": node.lineno, "symbol": arg.arg,
                                  "kind": "mutable-default"})
    class_attrs = {attr for _, attr in class_mutables}
    owners: dict[str, str] = {}
    for cls_name, attr in class_mutables:
        owners.setdefault(attr, cls_name)

    def _class_site(line: int, owner: str, attr: str):
        if attr in class_attrs and owner in ("self", "cls", owners.get(attr, "")):
            found.append({"line": line, "symbol": f"{owners[attr]}.{attr}",
                          "kind": "class-attribute"})

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Global):
                for name in stmt.names:
                    found.append({"line": stmt.lineno, "symbol": name,
                                  "kind": "module-global"})
            elif (isinstance(stmt, ast.Name)
                    and isinstance(stmt.ctx, ast.Store)
                    and stmt.id in module_mutables):
                found.append({"line": stmt.lineno, "symbol": stmt.id,
                              "kind": "module-global"})
            elif (isinstance(stmt, ast.Subscript)
                    and isinstance(stmt.ctx, ast.Store)
                    and isinstance(stmt.value, ast.Name)):
                if stmt.value.id in module_mutables:
                    found.append({"line": stmt.lineno, "symbol": stmt.value.id,
                                  "kind": "shared-cache"})
                elif stmt.value.id in default_names:
                    found.append({"line": stmt.lineno, "symbol": stmt.value.id,
                                  "kind": "mutable-default"})
            elif isinstance(stmt, ast.AugAssign):
                target = stmt.target
                if isinstance(target, ast.Name) and target.id in module_mutables:
                    found.append({"line": stmt.lineno, "symbol": target.id,
                                  "kind": "module-global"})
                elif (isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)):
                    _class_site(stmt.lineno, target.value.id, target.attr)
            elif isinstance(stmt, ast.Attribute) and isinstance(stmt.ctx, ast.Store):
                if isinstance(stmt.value, ast.Name):
                    _class_site(stmt.lineno, stmt.value.id, stmt.attr)
            elif isinstance(stmt, ast.Call) and isinstance(stmt.func, ast.Attribute):
                if stmt.func.attr in MUTATING_METHODS:
                    base = stmt.func.value
                    if isinstance(base, ast.Name):
                        if base.id in module_mutables:
                            found.append({"line": stmt.lineno, "symbol": base.id,
                                          "kind": "shared-cache"})
                        elif base.id in default_names:
                            found.append({"line": stmt.lineno, "symbol": base.id,
                                          "kind": "mutable-default"})
                    elif (isinstance(base, ast.Attribute)
                            and isinstance(base.value, ast.Name)):
                        _class_site(stmt.lineno, base.value.id, base.attr)
    seen_lines: set[int] = set()
    ordered = []
    for site in sorted(found, key=lambda s: s["line"]):
        if site["line"] not in seen_lines:
            seen_lines.add(site["line"])
            ordered.append(site)
    return ordered


def _fallback_sites(code: str) -> list[dict]:
    """`global X` line-scan for unparseable snippets."""
    found = []
    for i, line in enumerate((code or "").splitlines()):
        match = _GLOBAL_RE.match(line)
        if match:
            for raw in match.group(1).split(","):
                name = raw.strip()
                if name.isidentifier():
                    found.append({"line": i + 1, "symbol": name,
                                  "kind": "module-global"})
                    break
    return found


def find_sites(code: str) -> list[dict]:
    """Shared-state sites, earliest first. Never raises."""
    try:
        sites = _ast_sites(_tree(code or ""))
        if sites:
            return sites
        return _fallback_sites(code or "")
    except Exception:  # noqa: BLE001 — detection must never break generate
        return []


def _code_from(concept, snippet, ctx) -> str:
    ctx = ctx or {}
    code = str(ctx.get("runnable") or ctx.get("code_block")
               or "\n".join(snippet or []) or "").strip()
    return code or FALLBACK_CODE


def _concept_field(concept, name: str, default=""):
    return getattr(concept, name, default) or default


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a type-37 card; ungrounded when no shared state is found."""
    ctx = ctx or {}
    code = _code_from(concept, snippet, ctx)
    sites = find_sites(code)
    site = sites[0] if sites else None
    numbered = "\n".join(f"{i + 1}: {line}"
                         for i, line in enumerate(code.splitlines()))
    name = str(_concept_field(concept, "name", "func"))
    file = str(_concept_field(concept, "file", ""))
    try:
        line = int(_concept_field(concept, "line", 0))
    except (TypeError, ValueError):
        line = 0
    where = f"{file}:{line}" if file and line else (file or "the linked file")
    front = (
        f"Spot the shared-state race in `{name}`: which line reads or writes "
        f"shared mutable state (module global, shared cache, or mutable class "
        f"attribute)? Reply with the line number plus your fix — a local copy, "
        f"a lock, or a parameter. No threads are spawned; reason from the "
        f"code alone.\n```python\n{numbered[:CODE_LIMIT]}\n```"
    )
    if site is not None:
        fix = FIX_BY_KIND[site["kind"]]
        back = (f"Line {site['line']}: shared {site['kind']} "
                f"`{site['symbol']}`. Fix: {fix}.")
        payload = {"code": code, "numbered": numbered[:CODE_LIMIT],
                   "shared_line": site["line"], "symbol": site["symbol"],
                   "kind": site["kind"], "fix_keywords": list(FIX_KEYWORDS),
                   "grounded": True}
        hints = [
            "Shared state lives outside one call: module globals, caches, "
            "class attributes, mutable defaults.",
            f"Look at {where}: which line touches state every call shares?",
            f"Worked step: line {site['line']} touches shared "
            f"`{site['symbol']}` — now name the fix (copy, lock, parameter).",
        ]
    else:
        back = "No shared mutable state detected in this snippet."
        payload = {"code": code, "numbered": numbered[:CODE_LIMIT],
                   "shared_line": 0, "symbol": "", "kind": "",
                   "fix_keywords": list(FIX_KEYWORDS), "grounded": False}
        hints = [
            "Shared state lives outside one call: module globals, caches, "
            "class attributes, mutable defaults.",
            f"Look at {where}: does every call share the same object?",
            "Worked step: a `global` plus a mutation (or a mutable default) "
            "is the shape to look for.",
        ]
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
        "concept_id": str(_concept_field(concept, "node_id", name)),
        "concept": name, "file": file, "line": line,
        "commit": str(ctx.get("commit", "") or ""),
        "hints": hints, "front": front, "back": back, "payload": payload,
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Line-number match plus fix-keyword checklist. Never raises."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) if isinstance(exercise, dict) else {}
        want = int(payload.get("shared_line", 0) or 0)
        symbol = str(payload.get("symbol", "") or "")
    except (TypeError, ValueError, AttributeError):
        return _fail("This card is unreadable — flagged stale.")
    text = str(submission or "")
    if not text.strip():
        return _fail("Reply with the line number plus your fix "
                     "(local copy, lock, or parameter).")
    if not want:
        return _fail("This card has no shared-state site — flagged stale.")
    try:
        hits = re.findall(r"-?\d+", text)
        accused = int(hits[0]) if hits else None
    except (TypeError, ValueError):
        accused = None
    line_ok = accused == want
    lowered = text.lower()
    fix_ok = any(keyword in lowered for keyword in FIX_KEYWORDS)
    if line_ok and fix_ok:
        return {"pass": True, "score": 1.0,
                "feedback": f"Line {want} is the shared state (`{symbol}`); "
                            f"fix accepted."}
    if not line_ok and not fix_ok:
        return {"pass": False, "score": 0.0,
                "feedback": "Not that line — re-read the numbered snippet. "
                            "Also name the fix: local copy, lock, or parameter."}
    if not line_ok:
        return {"pass": False, "score": 0.5,
                "feedback": "Fix wording is on track, but that is not the "
                            "line — re-read the numbered snippet."}
    return {"pass": False, "score": 0.5,
            "feedback": f"Line {want} is right, but name the fix: local copy, "
                        f"lock, or parameter."}


def render(exercise: dict) -> str:
    """Card HTML: numbered snippet plus a line+fix textarea."""
    exercise = exercise or {}
    payload = exercise.get("payload", {}) if isinstance(exercise, dict) else {}
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    seed = html.escape("line: \nfix: ")
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", []))
    )
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Name the exact line number and propose a fix "
        f"(local copy, lock, or parameter). Both halves are required; "
        f"no code is executed.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='6' "
        f"cols='70'>{seed}</textarea>"
        f"<br><button>Submit line + fix</button></form>{hints}"
        f"<p><small>{html.escape(str(exercise.get('file', '')))}:"
        f"{exercise.get('line', 0)}</small></p></article>"
    )


def section_html(db_path: str = "") -> str:
    """Status-page home for this area (never in web.py)."""
    _ = db_path
    return ("<h3 id='status-b7-racehunt'>Race-hunt <small>(feature)</small></h3>"
            "<p>Type 37 exercises hand you a snippet with shared mutable "
            "state — name the line plus the fix (local copy, lock, or "
            "parameter), graded by line match and fix checklist with no "
            "threads spawned. <code>groundwork/racehunt.py</code>.</p>")


def tour_entry() -> dict:
    """Feature-tour registry entry for the parent to append."""
    return {"id": "racehunt-type", "kind": "feature",
            "title": "Race-hunt",
            "blurb": "Spot the shared mutable state: name the line plus "
                     "the fix — local copy, lock, or parameter.",
            "path": "/status", "anchor": "status-b7-racehunt"}
