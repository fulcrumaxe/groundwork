"""API-signature design exercise (type 40, F-17, bloom: create).

The learner designs a function signature — name, parameters with
defaults, return annotation — for a stated requirement anchored on the
concept. The reference points come from the concept's own real
definition when the snippet parses (parameter names, which of them
carry defaults and their literal values, whether a return annotation
exists); otherwise the card falls back to a name-only check.
Grading is a pure AST rubric check with partial credit — deterministic,
no execution, no sandbox runner. Stdlib only (``ast``/``html``/``re``),
import-safe standalone: no groundwork imports.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); see ===WIRES===.
"""
from __future__ import annotations

import ast
import copy
import html
import re

TYPE_NUM = 40
TYPE_NAME = "api-design"
BLOOM = "create"

_SKIP_PARAMS = ("self", "cls")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _slug(name: str) -> str:
    slug = re.sub(r"\W+", "_", name.strip()).strip("_").lower() or "func"
    if slug[0].isdigit():
        slug = "_" + slug
    return slug


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


def _ref_points(fn):
    """(required params, {param: default source}, want_return, return source)."""
    args = list(getattr(fn.args, "posonlyargs", [])) + list(fn.args.args)
    required = [a.arg for a in args + list(fn.args.kwonlyargs)
                if a.arg not in _SKIP_PARAMS]
    defaults: dict[str, str] = {}
    positionals = list(fn.args.args)
    n_defaulted = len(fn.args.defaults or [])
    for arg, node in zip(positionals[len(positionals) - n_defaulted:],
                         fn.args.defaults or []):
        if arg.arg not in _SKIP_PARAMS:
            defaults[arg.arg] = ast.unparse(node)
    for arg, node in zip(fn.args.kwonlyargs, fn.args.kw_defaults or []):
        if node is not None:
            defaults[arg.arg] = ast.unparse(node)
    want_return = fn.returns is not None
    ret_src = ast.unparse(fn.returns) if want_return else ""
    return required, defaults, want_return, ret_src


def _stub_of(fn) -> str:
    """Signature-only model answer: same header, `...` body."""
    head = copy.deepcopy(fn)
    head.body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
    ast.fix_missing_locations(head)
    mod = ast.Module(body=[head], type_ignores=[])
    return ast.unparse(mod)


def _param_prose(required: list[str], defaults: dict[str, str]) -> str:
    if not required:
        return "You choose the parameters — keep them minimal."
    bits = []
    for p in required:
        if p in defaults:
            bits.append(f"`{p}` (optional, default `{defaults[p]}`)")
        else:
            bits.append(f"`{p}` (required)")
    return "It must accept: " + "; ".join(bits) + "."


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build an api-design exercise: design a signature, not an implementation."""
    ctx = ctx or {}
    snippet = list(snippet or [])
    code = str(ctx.get("runnable") or "\n".join(snippet) or "").strip()
    name = _concept_field(concept, "name", "func")
    kind = _concept_field(concept, "kind", "function")
    file = _concept_field(concept, "file")
    try:
        line = int(getattr(concept, "line", 0) or 0)
    except (TypeError, ValueError):
        line = 0
    commit = str(ctx.get("commit", "") or "")
    fn = _find_fn(code, name) if code else None
    if fn is None:
        func = _slug(name)
        required: list[str] = []
        defaults: dict[str, str] = {}
        want_return, ret_src = False, ""
        reference = f"def {func}(...):\n    ..."
        grounded = False
    else:
        func = fn.name
        required, defaults, want_return, ret_src = _ref_points(fn)
        reference = _stub_of(fn)
        grounded = True
    purpose = (f"helps callers work with `{name}` "
               f"({kind}{f' in {file}' if file else ''})")
    lines = [f"Design the signature for a new function `{func}` that {purpose}."]
    lines.append(_param_prose(required, defaults))
    if want_return:
        lines.append("Annotate what it returns (`-> ...`).")
    lines.append("Reply with a single `def` stub — name, parameters with "
                 "defaults, return annotation; the body may be `...`.")
    front = "\n".join(lines)
    back = (reference + "  (model answer — any signature with the same "
            "names, defaults, and return annotation counts).")
    optionals = [p for p in required if p in defaults]
    hints = [
        f"Name it exactly `{func}` — callers will import that name.",
        ("Optional knobs: " + ", ".join(f"`{p}`" for p in optionals)
         + " — each needs a sensible default."
         if optionals else "Every parameter here is required — no defaults to invent."),
        ("End with a return annotation (`-> ...`) so callers know what "
         "comes back."
         if want_return else "No return annotation is needed — like the reference, it returns None."),
    ]
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
        "concept_id": _concept_field(concept, "node_id", name),
        "concept": name, "file": file, "line": line, "commit": commit,
        "hints": hints,
        "front": front, "back": back,
        "payload": {"func": func, "required": required, "defaults": defaults,
                    "want_return": want_return, "return": ret_src or None,
                    "reference": reference, "grounded": grounded},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _learner_points(fn):
    """(names present, {param: default source or None})."""
    args = list(getattr(fn.args, "posonlyargs", [])) + list(fn.args.args)
    names = {a.arg for a in args + list(fn.args.kwonlyargs)}
    if fn.args.vararg is not None:
        names.add(fn.args.vararg.arg)
    if fn.args.kwarg is not None:
        names.add(fn.args.kwarg.arg)
    got: dict[str, str | None] = {}
    positionals = list(fn.args.args)
    n_defaulted = len(fn.args.defaults or [])
    plain = positionals[:len(positionals) - n_defaulted]
    for a in plain + list(getattr(fn.args, "posonlyargs", [])):
        got.setdefault(a.arg, None)
    for arg, node in zip(positionals[len(positionals) - n_defaulted:],
                         fn.args.defaults or []):
        got[arg.arg] = ast.unparse(node)
    for arg, node in zip(fn.args.kwonlyargs, fn.args.kw_defaults or []):
        got[arg.arg] = ast.unparse(node) if node is not None else None
    return names, got


def _default_ok(ref_src: str, got_src: str | None) -> bool:
    """Sensible default: present, and equal when the reference is a literal."""
    if got_src is None:
        return False
    try:
        ref_val = ast.literal_eval(ref_src)
    except (ValueError, SyntaxError):
        return True  # non-literal reference: presence suffices
    try:
        return ast.literal_eval(got_src) == ref_val
    except (ValueError, SyntaxError):
        return False


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """AST rubric check: name, required params, defaults, return annotation.

    Pass needs every rubric point (like the typeanno sibling); the score
    still records partial credit. ``runner`` is accepted for API symmetry
    and ignored. Never raises: malformed input yields a failing grade,
    not an error.
    """
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {})
        func = str(payload.get("func", "") or "")
        required = list(payload.get("required", []) or [])
        defaults = dict(payload.get("defaults", {}) or {})
        want_return = bool(payload.get("want_return", False))
        text = str(submission or "").strip()
        if not text:
            return _fail("Submit a `def` stub with the designed signature.")
        try:
            tree = ast.parse(text)
        except (SyntaxError, ValueError):
            return _fail("Submission does not parse — submit a single `def` stub.")
        fns = [n for n in ast.walk(tree)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if not fns:
            return _fail("No function definition found in the submission.")
        fn = next((f for f in fns if f.name == func), fns[0])
        name_ok = bool(func) and fn.name == func
        names, got = _learner_points(fn)
        missing = []
        earned = 1 if name_ok else 0
        if not name_ok:
            missing.append(f"name should be `{func}`")
        total = 1 + len(required) + len(defaults) + (1 if want_return else 0)
        for p in required:
            if p in names:
                earned += 1
            else:
                missing.append(f"missing parameter `{p}`")
        for p, ref_src in defaults.items():
            if p in names and _default_ok(ref_src, got.get(p)):
                earned += 1
            else:
                missing.append(f"`{p}` needs default `{ref_src}`")
        if want_return:
            if fn.returns is not None:
                earned += 1
            else:
                missing.append("missing return annotation")
        score = earned / max(1, total)
        ok = bool(name_ok) and not missing
        detail = f"{earned}/{total} rubric points."
        if ok:
            return {"pass": True, "score": 1.0 if score == 1.0 else score,
                    "feedback": f"Signature accepted. {detail}"}
        return {"pass": False, "score": score,
                "feedback": f"Not yet. {detail} Fix: {'; '.join(missing)[:200]}."}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit a `def` stub.")


def render(exercise: dict) -> str:
    """Exercise widget: requirement plus a textarea seeded with `def <func>(`."""
    payload = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    seed = html.escape(f"def {payload.get('func', 'func')}(")
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", []))
    )
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>AST rubric: exact function name, required parameter "
        f"names, sensible defaults, and a return annotation when the "
        f"reference has one. Every point is required to pass; partial "
        f"credit is recorded, no sandbox.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='6' cols='70'>{seed}</textarea>"
        f"<br><button>Check signature</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b7-apidesign'>API-signature design <small>(feature)</small></h3>"
        "<p>Design a function signature — name, parameters with defaults, "
        "return annotation — for a stated requirement. Graded by AST rubric "
        "check with partial credit, no sandbox. "
        "<code>groundwork/apidesign.py</code>.</p>"
    )
