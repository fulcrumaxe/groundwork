"""Config-extraction exercises (type 39, F-16, modify).

The learner moves magic numbers/strings out of a function body into
named module-level constants (UPPER_SNAKE names or a CONFIG dict), so
the code reads as intent instead of literals. Grading mirrors the
sibling modify types (19/20/27): an AST check that the recorded magic
literals are gone from function bodies and live in named constants,
plus a sandbox harness run proving behavior is identical.

Pure functions, stdlib only, import-safe standalone: nothing here
imports groundwork. Registration (done by the parent, see WIRES):
TYPES/GENERATORS/BLOOM_TYPES plus delegate branches in
exercises.render/grade, pipeline emission, one status.py include,
one tour entry.
"""
from __future__ import annotations

import ast
import html
import re

TYPE_NUM = 39
TYPE_NAME = "config-extract"
BLOOM = "modify"
AREA_KEY = "configex"

_SKIP_NUMBERS = {0, 1, -1, 0.0, 1.0}


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _func_node(tree, fn_name: str):
    fns = [n for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for n in fns:
        if n.name == fn_name:
            return n
    return fns[0] if fns else None


def _is_magic(value) -> bool:
    """A literal worth naming: excludes None/bools, 0/1/-1, blank strings."""
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return value not in _SKIP_NUMBERS
    if isinstance(value, str):
        return bool(value.strip())
    return False


def _key(value) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def _docstring_ids(fn) -> set[int]:
    if (fn.body and isinstance(fn.body[0], ast.Expr)
            and isinstance(fn.body[0].value, ast.Constant)
            and isinstance(fn.body[0].value.value, str)):
        return {id(fn.body[0].value)}
    return set()


def _fn_magic_values(fn) -> list:
    """Distinct magic values used inside one function, docstring excluded."""
    skip = _docstring_ids(fn)
    seen, out = set(), []
    for n in ast.walk(fn):
        if id(n) in skip:
            continue
        if isinstance(n, ast.Constant) and _is_magic(n.value):
            k = _key(n.value)
            if k not in seen:
                seen.add(k)
                out.append(n.value)
    return out


def _const_name(value, taken: set) -> str:
    """Deterministic UPPER_SNAKE name for a magic value."""
    if isinstance(value, str):
        base = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_").upper()[:24]
        base = base or "TEXT"
    elif isinstance(value, float):
        base = ("N_NEG" if value < 0 else "N_") + repr(abs(value)).replace(".", "P")
        base = re.sub(r"[^A-Za-z0-9]+", "_", base).upper()
    else:
        base = ("N_NEG" if value < 0 else "N_") + str(abs(value))
    if not base[:1].isalpha():
        base = "C_" + base
    name, i = base, 2
    while name in taken:
        name = f"{base}_{i}"
        i += 1
    taken.add(name)
    return name


def _extract_reference(body: str, mapping: dict) -> str:
    """Reference solution: constants hoisted, bodies rewritten via AST."""
    try:
        tree = ast.parse(body)
    except (SyntaxError, ValueError):
        return body
    skip: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            skip |= _docstring_ids(n)

    class _Hoist(ast.NodeTransformer):
        def visit_Constant(self, node):  # noqa: N802 — AST visitor naming
            if id(node) in skip or not _is_magic(node.value):
                return node
            name = mapping.get(_key(node.value))
            if name is None:
                return node
            return ast.copy_location(ast.Name(id=name, ctx=ast.Load()), node)

    try:
        rewritten = ast.unparse(_Hoist().visit(tree))
    except (ValueError, SyntaxError):
        return body
    consts = [f"{name} = {_k[1]}" for _k, name in mapping.items()]
    return "\n".join(consts + ["", "", rewritten])


def should_emit(ctx) -> bool:
    """Emission guard: needs the measured harness, like types 26/27."""
    return "tests" in (ctx or {})


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build the type-39 exercise dict (engine shape, standalone)."""
    ctx = ctx or {}
    body = (ctx.get("runnable") or "\n".join(snippet or [])
            or f"def {getattr(concept, 'name', 'func')}():\n    return 42")
    fname = _concept_field(concept, "name", "func") or "func"
    try:
        fn = _func_node(ast.parse(body), fname)
    except (SyntaxError, ValueError):
        fn = None
    magics = _fn_magic_values(fn) if fn is not None else []
    taken: set = set()
    mapping = {_key(v): _const_name(v, taken) for v in magics}
    reference = _extract_reference(body, mapping) if magics else body
    tests = ctx.get("tests", "")
    names = sorted(mapping.values())
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": _concept_field(concept, "node_id", fname),
        "concept": fname, "file": _concept_field(concept, "file"),
        "line": getattr(concept, "line", 0) or 0,
        "commit": str(ctx.get("commit", "") or ""),
        "hints": [
            f"Name each magic literal inside `{fname}` before changing anything.",
            f"Hoist them to module level ({', '.join(names) or 'UPPER_SNAKE names'}"
            " or a CONFIG dict); the function body keeps the names, not the literals.",
            "Worked step: `RATE = 0.2` at module level, `n * RATE` in the body — "
            "the hidden tests prove nothing else changed.",
        ],
        "front": f"Move the magic values out of `{fname}` into named constants "
                 f"({', '.join(names) or 'UPPER_SNAKE names'} or a CONFIG dict) — "
                 f"behavior must stay identical.\n```python\n{body[:600]}\n```",
        "back": reference,
        "payload": {"func": fname, "original": body, "reference": reference,
                    "magics": sorted(k[1] for k in mapping),
                    "consts": {k[1]: name for k, name in mapping.items()},
                    "tests": tests,
                    "grounded": bool(tests) and bool(magics)},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _wanted_values(payload: dict) -> list:
    out = []
    for rep in payload.get("magics", []) or []:
        try:
            out.append(ast.literal_eval(rep))
        except (ValueError, SyntaxError):
            continue
    return [v for v in out if _is_magic(v)]


def _module_constant_keys(tree) -> set:
    """(typename, repr) keys held by module-level UPPER_SNAKE/CONFIG names."""
    found = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            exprs = [node.value]
        elif (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                and node.value is not None):
            targets = [node.target.id]
            exprs = [node.value]
        else:
            continue
        if not any(t.isupper() for t in targets):
            continue
        for e in exprs:
            vals = list(e.values) if isinstance(e, ast.Dict) else [e]
            for v in vals:
                try:
                    lit = ast.literal_eval(v)
                except (ValueError, SyntaxError):
                    continue
                if _is_magic(lit):
                    found.add(_key(lit))
    return found


def _remaining_magic(fn, wanted: list):
    """First bare magic literal still inside a function body, else None."""
    skip = _docstring_ids(fn)
    for n in ast.walk(fn):
        if id(n) in skip or not isinstance(n, ast.Constant):
            continue
        for w in wanted:
            if type(n.value) is type(w) and n.value == w:
                return w
    return None


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Named constants extracted plus a green harness where one exists."""
    payload = (exercise or {}).get("payload", {})
    wanted = _wanted_values(payload)
    text = str(submission or "")
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return _fail("Submission does not parse — resubmit valid Python.")
    fns = [n for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not fns:
        return _fail("No function definition found.")
    if wanted:
        held = _module_constant_keys(tree)
        missing = [w for w in wanted if _key(w) not in held]
        if missing:
            return _fail(f"No named module-level constant holds {missing[0]!r} — "
                         "hoist each literal to an UPPER_SNAKE name or a CONFIG dict.")
        for fn in fns:
            left = _remaining_magic(fn, wanted)
            if left is not None:
                return _fail(f"Magic `{left!r}` is still inline in "
                             f"`{fn.name}` — use the named constant instead.")
    tests = payload.get("tests", "")
    if not tests:
        return {"pass": True, "score": 1.0,
                "feedback": "Magics extracted to named constants "
                            "(no harness on this card)."}
    if runner is None:
        return _fail("No sandbox available for grading.")
    try:
        res = runner.run(text + "\n" + tests)
    except Exception as exc:  # noqa: BLE001 — runner failure is feedback, not a crash
        return _fail(f"Harness could not run: {exc}")
    ok = bool(res.ok) and "FAIL" not in str(res.stdout)
    if ok:
        return {"pass": True, "score": 1.0,
                "feedback": "Extracted and green — behavior identical."}
    return {"pass": False, "score": 0.0,
            "feedback": f"Behavior changed: {str(res.stdout)[:200]} {str(res.stderr)[:200]}".strip()}


def render(exercise: dict) -> str:
    """Exercise card HTML (mirrors exercises.render article wrapper)."""
    p = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    body = f"<p>{front}</p>"
    body += ("<details><summary>How grading works</summary>"
             "<p><small>Magic literals must be gone from function bodies, "
             "named constants must hold them, and the hidden tests must stay green."
             "</small></p></details>"
             "<form method='post'><textarea name='answer' rows='12' "
             f"cols='70'>{html.escape(str(p.get('original', '')))}</textarea>"
             "<br><button>Run tests</button></form>")
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (f"<article><h3>{html.escape(str(exercise.get('concept', '')))} "
            f"· {html.escape(str(exercise.get('type_name', TYPE_NAME)))}</h3>"
            f"{body}{hints}"
            f"<p><small>{html.escape(str(exercise.get('file', '')))}:"
            f"{exercise.get('line', 0)}</small></p></article>")


def section_html(db_path: str = "") -> str:
    """Status-page home for this area (never in web.py)."""
    _ = db_path
    return (
        "<h3 id='status-b7-configex'>Config extraction <small>(feature)</small></h3>"
        "<p>Move magic numbers and strings into named constants — graded by AST "
        "plus a green harness proving behavior is identical. "
        "<code>groundwork/configex.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "configex-type", "kind": "feature",
            "title": "Config extraction",
            "blurb": "Hoist magic values into named constants; hidden tests stay green.",
            "path": "/status", "anchor": "status-b7-configex"}
