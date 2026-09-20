"""Dependency-injection swap exercises (F-5, type 27, modify).

The learner rewrites a hardcoded dependency as an injected parameter
whose default is the original symbol, so old callers and hidden tests
stay green. Nearest sibling: type 20 (extend-feature), which checks an
optional parameter plus a green harness; this type additionally pins
the default to the original dependency.

Pure functions, stdlib only, import-safe standalone: nothing here
imports groundwork. Registration (done by the parent, see WIRES):
TYPES/GENERATORS/BLOOM_TYPES plus delegate branches in
exercises.render/grade, one grading.disclosure line, one status.py
include, one tour entry.
"""
from __future__ import annotations

import ast
import html
import keyword

TYPE_NUM = 27
TYPE_NAME = "dependency-injection"
BLOOM = "modify"

_FALLBACK_DEP = "today"

_BUILTINS = {
    "print", "len", "range", "str", "int", "float", "bool",
    "list", "dict", "set", "tuple", "sum", "min", "max", "abs",
    "sorted", "enumerate", "zip", "map", "filter", "repr",
    "isinstance", "hasattr", "getattr", "open", "ValueError",
    "TypeError", "KeyError", "RuntimeError", "Exception",
    "NotImplementedError", "StopIteration",
}


def _func_node(body: str, fn_name: str):
    """AST node of fn_name, else the first function, else None."""
    try:
        tree = ast.parse(body)
    except (SyntaxError, ValueError):
        return None
    fns = [n for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for n in fns:
        if n.name == fn_name:
            return n
    return fns[0] if fns else None


def _called_globals(body: str) -> list[str]:
    """Called names that are not params, locals, imports or builtins."""
    try:
        tree = ast.parse(body)
    except (SyntaxError, ValueError):
        return []
    bound = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            bound.add(n.name)
            args = list(n.args.args) + list(n.args.kwonlyargs)
            for a in args:
                bound.add(a.arg)
            if n.args.vararg is not None:
                bound.add(n.args.vararg.arg)
            if n.args.kwarg is not None:
                bound.add(n.args.kwarg.arg)
        elif isinstance(n, ast.Name) and isinstance(
                n.ctx, (ast.Store, ast.Del)):
            bound.add(n.id)
        elif isinstance(n, ast.Import):
            for a in n.names:
                bound.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            for a in n.names:
                bound.add(a.asname or a.name)
    seen, out = set(), []
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id not in bound
                and n.func.id not in _BUILTINS
                and n.func.id not in seen):
            seen.add(n.func.id)
            out.append(n.func.id)
    return out


def _param_for(dep: str, taken: list[str]) -> str:
    """Parameter name for dep; never a keyword or a collision."""
    base = "".join(c if c.isidentifier() or c == "_" else "_"
                   for c in dep).strip("_") or "dep"
    if not base.isidentifier() or keyword.iskeyword(base):
        base = "dep"
    if base in taken:
        base += "_fn"
    return base


def _default_pairs(fn):
    """(arg, default) pairs with positional defaults tail-aligned."""
    positional = list(fn.args.args)
    defaults = list(fn.args.defaults or [])
    pairs = list(zip(positional[len(positional) - len(defaults):], defaults))
    pairs += list(zip(fn.args.kwonlyargs, fn.args.kw_defaults or []))
    return pairs


def _has_default_param(fn, param: str) -> bool:
    """True when fn defines param with a default value (optional)."""
    positional = list(fn.args.args)
    defaults = list(fn.args.defaults or [])
    if defaults:
        for arg, default in zip(
                positional[len(positional) - len(defaults):], defaults):
            if arg.arg == param and default is not None:
                return True
    for arg, default in zip(fn.args.kwonlyargs, fn.args.kw_defaults or []):
        if arg.arg == param and default is not None:
            return True
    return False


def _default_mentions(fn, param: str, dep: str) -> bool:
    """True when param's default still names the original dep."""
    for arg, default in _default_pairs(fn):
        if arg.arg == param and default is not None:
            return any(isinstance(n, ast.Name) and n.id == dep
                       for n in ast.walk(default))
    return False


def _inject_reference(body: str, fn_name: str, dep: str, param: str) -> str:
    """Signature rewritten with `param=dep`; body untouched.

    The default binds the original at def time, so old callers keep
    working. Returns body unchanged when the rewrite is not safe.
    """
    lines = body.splitlines() or [f"def {fn_name}():"]
    idx = next((i for i, line in enumerate(lines)
                if line.strip().startswith(f"def {fn_name}")
                and "(" in line), None)
    if idx is None:
        return body
    head, sep, tail = lines[idx].rpartition(")")
    if not sep:
        return body
    glue = "" if head.rstrip().endswith("(") else ", "
    lines[idx] = f"{head}{glue}{param}={dep}){tail}"
    candidate = "\n".join(lines)
    try:
        tree = ast.parse(candidate)
    except (SyntaxError, ValueError):
        return body
    fn = _func_node(candidate, fn_name)
    if fn is None or not _has_default_param(fn, param):
        return body
    return candidate


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build the type-27 exercise dict (engine shape, standalone)."""
    ctx = ctx or {}
    body = (ctx.get("runnable") or "\n".join(snippet or [])
            or f"def {concept.name}():\n    pass")
    fn = _func_node(body, concept.name)
    taken = ([a.arg for a in fn.args.args] +
             [a.arg for a in fn.args.kwonlyargs]) if fn is not None else []
    dep = ctx.get("dep") or next(iter(_called_globals(body)), None)
    if not dep or not str(dep).isidentifier():
        dep = _FALLBACK_DEP
    param = ctx.get("dep_param") or _param_for(dep, taken)
    reference = _inject_reference(body, concept.name, dep, param)
    tests = ctx.get("tests", "")
    ex = {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": concept.node_id,
        "concept": concept.name, "file": concept.file,
        "line": concept.line, "commit": ctx.get("commit", ""),
        "hints": [
            f"Name where `{dep}` is fixed inside `{concept.name}` "
            "before changing anything.",
            f"Add `{param}={dep}` to the signature; the body can keep "
            f"calling `{dep}`.",
            f"Worked step: `def {concept.name}(..., {param}={dep})` keeps "
            "old callers green — the hidden tests prove it.",
        ],
    }
    ex.update(
        front=f"Rewrite `{concept.name}` so its hardcoded `{dep}` arrives "
        f"as a parameter `{param}={dep}` — old callers must keep working.\n"
        f"```python\n{body[:600]}\n```",
        back=reference,
        payload={"dep": dep, "param": param, "func": concept.name,
                 "original": body, "reference": reference,
                 "tests": tests, "grounded": bool(tests)})
    return ex


def render(exercise: dict) -> str:
    """Exercise card HTML (mirrors exercises.render article wrapper)."""
    p = exercise.get("payload", {})
    front = html.escape(exercise.get("front", ""))
    body = f"<p>{front}</p>"
    body += ("<form method='post'><textarea name='answer' rows='12' "
             f"cols='70'>{html.escape(p.get('original', ''))}</textarea>"
             "<br><button>Run tests</button></form>")
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (f"<article><h3>{html.escape(exercise.get('concept', ''))} "
            f"· {html.escape(exercise.get('type_name', TYPE_NAME))}</h3>"
            f"{body}{hints}"
            f"<p><small>{html.escape(exercise.get('file', ''))}:"
            f"{exercise.get('line', 0)}</small></p></article>")


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """AST-checked injection plus a green harness where one exists."""
    p = exercise.get("payload", {})
    dep = p.get("dep", _FALLBACK_DEP)
    param = p.get("param", dep)
    func = p.get("func", "")
    try:
        tree = ast.parse(submission)
    except (SyntaxError, ValueError):
        return {"pass": False, "score": 0.0,
                "feedback": "Submission does not parse — resubmit valid Python."}
    fns = [n for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    fn = next((n for n in fns if n.name == func), None)
    if fn is None:
        fn = fns[0] if fns else None
    if fn is None:
        return {"pass": False, "score": 0.0,
                "feedback": "No function definition found."}
    if not _has_default_param(fn, param):
        return {"pass": False, "score": 0.0,
                "feedback": f"No injected parameter `{param}=...` found — "
                            f"add it with the original `{dep}` as default."}
    if not _default_mentions(fn, param, dep):
        return {"pass": False, "score": 0.0,
                "feedback": f"Default must be the original `{dep}` so old "
                            "callers keep working."}
    tests = p.get("tests", "")
    if not tests:
        return {"pass": True, "score": 1.0,
                "feedback": f"Injected `{param}={dep}`; defaults preserved "
                            "(no harness on this card)."}
    if runner is None:
        return {"pass": False, "score": 0.0,
                "feedback": "No sandbox available for grading."}
    res = runner.run(submission + "\n" + tests)
    ok = res.ok and "FAIL" not in res.stdout
    return {"pass": ok, "score": 1.0 if ok else 0.0,
            "feedback": "Injected and green — old behavior kept."
            if ok else f"Old behavior broke: {res.stdout[:300]} {res.stderr[:300]}"}


def section_html(db_path: str = "") -> str:
    """Status-page home for this area (never in web.py)."""
    return ("<h2 id='status-b6-diretro'>Dependency-injection swap</h2>"
            "<p>Type 27 (<code>modify</code>): rewrite a hardcoded "
            "dependency as an injected parameter defaulting to the "
            "original; hidden tests stay green. "
            "<code>groundwork/diretro.py</code>.</p>")


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "diretro-swap", "kind": "feature",
            "title": "Dependency-injection swap",
            "blurb": "Rewrite a hardcoded dependency as a parameter; "
                     "old tests stay green.",
            "path": "/status", "anchor": "status-b6-diretro"}
