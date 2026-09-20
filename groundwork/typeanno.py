"""Type-annotation retrofit exercises (F-8, type 31, bloom: apply).

The learner gets a working but unannotated function and adds parameter
+ return annotations. Grading is a pure AST verifier — each annotation
slot is normalized (case / ``typing.`` prefix / alias-insensitive) and
compared against the reference, with partial credit per slot. No sandbox
runner is needed. Stdlib only; import-safe standalone (imports nothing
from the package so ``exercises.py`` can delegate without cycles).
"""
from __future__ import annotations

import ast
import html

TYPE_NUM = 31
TYPE_NAME = "type-annotation"
BLOOM = "apply"

_SKIP_PARAMS = ("self", "cls")

# Whole-annotation spelling aliases, applied after lowercasing.
_ALIAS = {
    "integer": "int",
    "string": "str",
    "boolean": "bool",
    "double": "float",
    "none": "None",
    "nonetype": "None",
    "null": "None",
}


def norm_ann(src: str) -> str:
    """Normalize one annotation for comparison."""
    try:
        text = ast.unparse(ast.parse(src.strip(), mode="eval").body)
    except (SyntaxError, ValueError):
        text = src
    text = text.strip().lower().replace("typing.", "")
    return _ALIAS.get(text, text)


def _slots_of(fn) -> tuple[dict[str, str | None], str | None]:
    """{param: raw annotation or None}, plus raw return annotation."""
    params: dict[str, str | None] = {}
    args = list(getattr(fn.args, "posonlyargs", [])) + list(fn.args.args)
    for a in args:
        if a.arg in _SKIP_PARAMS:
            continue
        params[a.arg] = ast.unparse(a.annotation) if a.annotation else None
    for a in fn.args.kwonlyargs:
        params[a.arg] = ast.unparse(a.annotation) if a.annotation else None
    ret = ast.unparse(fn.returns) if fn.returns else None
    return params, ret


def _find_fn(code: str, name: str):
    """FunctionDef named `name`, else the first def; None if unparseable."""
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return None
    fns = [n for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not fns:
        return None
    return next((f for f in fns if f.name == name), fns[0])


def _strip_fn(fn) -> str:
    """Source of `fn` with every annotation removed."""
    for a in (list(getattr(fn.args, "posonlyargs", [])) + list(fn.args.args)
              + list(fn.args.kwonlyargs)):
        a.annotation = None
    if fn.args.vararg is not None:
        fn.args.vararg.annotation = None
    if fn.args.kwarg is not None:
        fn.args.kwarg.annotation = None
    fn.returns = None
    return ast.unparse(fn)


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Strip a real annotated def; the reference is the original."""
    ctx = ctx or {}
    code = ctx.get("runnable") or "\n".join(snippet or []) or ""
    fn = _find_fn(code, concept.name)
    commit = ctx.get("commit", "") if isinstance(ctx, dict) else ""
    ex = {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
        "concept_id": concept.node_id, "concept": concept.name,
        "file": concept.file, "line": concept.line, "commit": commit,
        "hints": [
            f"Annotate every parameter of `{concept.name}` first; the return last.",
            f"Re-read the body — what types flow in, what type comes out?",
            "Worked step: `def f(x): return str(x)` becomes `def f(x: int) -> str`.",
        ],
    }
    if fn is None:
        ex.update(
            front=f"Add type annotations to `{concept.name}` (params + return).",
            back="No parseable function found in the snippet.",
            payload={"func": concept.name, "slots": [], "want_return": False,
                     "annotations": {}, "returns": None, "stripped": code,
                     "reference": code, "grounded": False})
        return ex
    params, ret = _slots_of(fn)
    have = {k: norm_ann(v) for k, v in params.items() if v}
    have_ret = norm_ann(ret) if ret else None
    lines = code.splitlines()
    try:
        ref = "\n".join(lines[fn.lineno - 1:fn.end_lineno])
    except (AttributeError, TypeError):
        ref = code
    if not have and not have_ret:
        ex.update(
            front=f"Add type annotations to `{concept.name}` — every parameter "
            f"and the return value.\n```python\n{ast.unparse(fn)}\n```",
            back=ref,
            payload={"func": fn.name, "slots": sorted(params),
                     "want_return": True, "annotations": {},
                     "returns": None, "stripped": ast.unparse(fn),
                     "reference": ref, "grounded": False})
        return ex
    stripped = _strip_fn(fn)
    ex.update(
        front=f"Add type annotations to `{fn.name}` — every parameter and "
        f"the return value.\n```python\n{stripped}\n```",
        back=ref,
        payload={"func": fn.name, "slots": sorted(params),
                 "want_return": ret is not None, "annotations": have,
                 "returns": have_ret, "stripped": stripped,
                 "reference": ref, "grounded": True})
    return ex


def render(exercise: dict) -> str:
    """Card HTML: prompt, stripped code, answer textarea, hints."""
    p = exercise.get("payload", {})
    front = html.escape(exercise.get("front", ""))
    stripped = html.escape(p.get("stripped", ""))
    body = (f"<p>{front}</p>"
            f"<form method='post'><textarea name='answer' rows='12' cols='70'>"
            f"{stripped}</textarea><br><button>Annotate</button></form>")
    hints = "".join(f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
                    for i, h in enumerate(exercise.get("hints", [])))
    return (f"<article><h3>{html.escape(exercise.get('concept', ''))} "
            f"· {html.escape(exercise.get('type_name', TYPE_NAME))}</h3>"
            f"{body}{hints}"
            f"<p><small>{html.escape(exercise.get('file', ''))}:{exercise.get('line', 0)}</small></p></article>")


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """AST-compare each annotation slot; partial credit per slot."""
    _ = runner  # verifier needs no sandbox.
    p = exercise.get("payload", {})
    want: dict = p.get("annotations", {})
    want_ret = p.get("returns")
    slots: list = p.get("slots", list(want))
    try:
        tree = ast.parse(str(submission))
    except (SyntaxError, ValueError):
        return {"pass": False, "score": 0.0,
                "feedback": "Submission does not parse — submit the full annotated function."}
    fns = [n for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not fns:
        return {"pass": False, "score": 0.0,
                "feedback": "No function definition found in the submission."}
    fn = next((f for f in fns if f.name == p.get("func")), fns[0])
    got_params, got_ret = _slots_of(fn)
    total = len(slots) + (1 if p.get("want_return") else 0)
    if total == 0:
        return {"pass": False, "score": 0.0,
                "feedback": "This card carries no reference annotations."}
    wrong = []
    for name in slots:
        raw = got_params.get(name)
        if raw is None or (name in want and norm_ann(raw) != want[name]):
            wrong.append(name)
    if p.get("want_return"):
        if (got_ret is None) != (want_ret is None) or (
                got_ret is not None and want_ret is not None
                and norm_ann(got_ret) != want_ret):
            wrong.append("return")
    ok = not wrong
    score = (total - len(wrong)) / total
    return {"pass": ok, "score": score,
            "feedback": "All annotations match." if ok else
            f"Slot(s) {wrong} differ — check the body for what flows in and out."}


def section_html(db_path: str = "") -> str:
    """Status-page subsection; always renders so the anchor never moves."""
    _ = db_path  # static section: no queries.
    return ("<h2 id='status-b6-typeanno'>Type-annotation retrofit</h2>"
            "<p>Exercise type 31 (apply): annotate an unannotated function — "
            "every parameter plus the return. Graded by AST comparison "
            "(spelling-normalized), partial credit per slot, no sandbox.</p>")
