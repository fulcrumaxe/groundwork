"""Rename-symbol exercise (type 17): propose a better name.

TYPES entries are kebab-case nouns naming the task
("signature-recall", "where-live", "blast-radius", "odd-one-out").
"rename-symbol" matches that convention; "rename-refactor" overclaims
(refactor-under-test, type 19, already owns behaviour-preserving
rewrites, and this type never runs code).

The learner renames one weak identifier (single-letter or vague name)
found in the snippet. Grading is convention + peer rubric, mirroring
the sibling families: automatic snake_case/meaningfulness checks
(convention half) plus a keyword checklist over the one-line
justification (rubric half, same >= 1/2 bar as types 5/6/21/24/25).
Pure functions, stdlib only. No groundwork imports at module level,
so this file is import-safe standalone; registration happens in
groundwork/exercises.py (see WIRES).
"""
from __future__ import annotations

import ast
import builtins
import html
import keyword
import re

TYPE_NUM = 17
TYPE_NAME = "rename-symbol"
BLOOM = "analyse"

# Vague-but-legal names worth renaming even when longer than 1 char.
WEAK_NAMES = frozenset({
    "tmp", "temp", "foo", "bar", "baz", "val", "var", "obj",
    "data", "info", "stuff", "thing", "item", "elem", "res",
})

TOUR_ENTRY = {
    "id": "rename-exercise", "kind": "feature",
    "title": "Rename-symbol exercise",
    "blurb": "Propose a clearer name for a weak identifier; "
             "convention-checked, rubric-justified.",
    "path": "/status", "anchor": "status-b6-renameex",
}


def _field(concept, name: str, default=""):
    if isinstance(concept, dict):
        return concept.get(name, default)
    return getattr(concept, name, default)


def _locals_in_order(code: str) -> list[tuple[str, str]]:
    """(name, kind) locals in first-appearance order; skips _private."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    found: list[tuple[str, str]] = []

    def add(name: str, kind: str):
        if (name not in ("self", "cls") and not name.startswith("_")
                and name.isidentifier()
                and all(n != name for n, _ in found)):
            found.append((name, kind))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for a in list(node.args.args) + list(node.args.kwonlyargs):
                add(a.arg, "parameter")
        elif isinstance(node, ast.For):
            for n in ast.walk(node.target):
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                    add(n.id, "variable")
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                        add(n.id, "variable")
    return found


def _weakness(name: str) -> int:
    if len(name) <= 1:
        return 0
    if name in WEAK_NAMES or name.lower() in WEAK_NAMES:
        return 1
    return 2


def pick_target(code: str, concept_name: str = "") -> tuple[str, str, bool]:
    """(name, kind, grounded): weakest local, or concept fallback.

    Ties break toward assigned variables over parameters (renaming the
    accumulator teaches more than renaming ``a`` in ``add(a, b)``),
    then by first appearance.
    """
    locals_ = _locals_in_order(code)
    cands = [(n, k) for n, k in locals_ if n != concept_name]
    if cands:
        rank = {"variable": 0, "parameter": 1}
        name, kind = min(
            cands,
            key=lambda nk: (_weakness(nk[0]), rank.get(nk[1], 2),
                            cands.index(nk)))
        return name, kind, _weakness(name) < 2
    if concept_name:
        return concept_name, "function", False
    return "", "", False


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build the type-17 exercise dict (same keys as exercises._base)."""
    from groundwork.exercises import TYPES  # lazy: keeps module standalone
    ctx = ctx or {}
    code = "\n".join(snippet or [])
    name, bloom = TYPES.get(TYPE_NUM, (TYPE_NAME, BLOOM))
    override = ctx.get("rename_target", "")
    if isinstance(override, dict):
        target, kind, grounded = (override.get("name", ""),
                                  override.get("kind", "variable"), True)
    elif isinstance(override, str) and override.strip():
        target, kind, grounded = override.strip(), "variable", True
    else:
        target, kind, grounded = pick_target(code, _field(concept, "name", ""))
    concept_name = _field(concept, "name", "")
    file_ = _field(concept, "file", "")
    line = _field(concept, "line", 0)
    rubric = [r for r in (concept_name, kind,
                          file_.split("/")[-1] if file_ else "") if r]
    if code.strip():
        front = (f"Propose a better name for `{target}` ({kind}) — "
                 f"then one line saying why it fits.\n```python\n{code[:800]}\n```")
    else:
        front = (f"Propose a better name for `{target}` ({kind}) — "
                 f"then one line saying why it fits.")
    where = f"{file_}:{line}" if file_ and line else (file_ or "the snippet")
    hints = [f"Say what `{target}` holds or does, then put that word in the name.",
             f"Look at {where}.",
             "Worked step: a reviewer should guess the role from the name "
             "alone — snake_case, 3+ characters, no shadowing."]
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": name, "bloom": bloom,
        "concept_id": _field(concept, "node_id", ""),
        "concept": concept_name, "file": file_, "line": line,
        "commit": ctx.get("commit", ""), "hints": hints,
        "front": front,
        "back": f"Rename `{target}` to an intention-revealing snake_case "
                f"name and justify it against: {', '.join(rubric) or target}.",
        "payload": {"target": target, "kind": kind, "code": code[:800],
                    "rubric": rubric, "grounded": grounded},
    }


def convention_failures(proposed: str, target: str = "") -> list[str]:
    """Machine half of the grade: naming-convention violations."""
    fails: list[str] = []
    if not proposed.isidentifier():
        fails.append(f"`{proposed}` is not a valid Python name.")
        return fails
    if re.fullmatch(r"[a-z][a-z0-9_]*", proposed) is None or "__" in proposed:
        fails.append("Use snake_case: lowercase letters, digits, "
                     "single underscores.")
    if len(proposed) < 3:
        fails.append("Too short to carry meaning — aim for 3+ characters.")
    if proposed in keyword.kwlist or proposed in dir(builtins):
        fails.append(f"`{proposed}` shadows a keyword or builtin.")
    if target:
        tn, nn = target.strip().lower(), proposed.lower()
        if nn == tn:
            fails.append("That is the current name — propose something new.")
        elif re.fullmatch(re.escape(tn) + r"_?\d+", nn) is not None:
            fails.append("Appending digits does not explain the role.")
    return fails


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Grade -> {pass, score, feedback}; no sandbox needed (runner ignored)."""
    p = exercise.get("payload", {}) if isinstance(exercise, dict) else {}
    target = p.get("target", "")
    text = str(submission or "").strip()
    if not text:
        return {"pass": False, "score": 0.0,
                "feedback": "Propose a new name plus one line saying why it fits."}
    tokens = text.split()
    proposed = tokens[0].strip(",:;-")
    reason = text[len(tokens[0]):]
    fails = convention_failures(proposed, target)
    rubric = [r for r in p.get("rubric", []) if r]
    lowered = reason.lower()
    hits = [r for r in rubric if r.lower() in lowered]
    total = max(1, len(rubric))
    rub = len(hits) / total
    conv = max(0.0, 1.0 - 0.25 * len(fails))
    score = round(0.5 * conv + 0.5 * rub, 2)
    ok = not fails and rub >= 0.5
    if ok:
        return {"pass": True, "score": 1.0,
                "feedback": "Clear name, well justified."}
    detail = list(fails)
    if rub < 0.5:
        missing = [r for r in rubric if r.lower() not in lowered]
        detail.append(f"Justify it: mention {', '.join(missing)[:120]} "
                      f"({len(hits)}/{total} key points).")
    return {"pass": False, "score": score, "feedback": " ".join(detail)}


def render(exercise: dict) -> str:
    """Single-answer form (one textarea: name + why), sibling-styled."""
    p = exercise.get("payload", {}) if isinstance(exercise, dict) else {}
    front = html.escape(exercise.get("front", ""))
    code = html.escape(p.get("code", ""))
    body = f"<p>{front}</p>"
    if code and code not in front:
        from . import codelines as codelinesmod
        body += f"<pre><code>{codelinesmod.numbered_html(p.get('code', ''))}</code></pre>"
    body += ("<form method='post'><textarea name='answer' rows='3' cols='70' "
             "placeholder='new_name — why it fits'></textarea><br>"
             "<button>Submit</button></form>")
    hints = "".join(f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
                    for i, h in enumerate(exercise.get("hints", [])))
    return (f"<article><h3>{html.escape(exercise.get('concept', ''))} "
            f"· {html.escape(exercise.get('type_name', ''))}</h3>"
            f"{body}{hints}"
            f"<p><small>{html.escape(exercise.get('file', ''))}:{exercise.get('line', 0)}</small></p></article>")


def section_html(db_path: str = "") -> str:
    """Status subsection for type 17 (anchor status-b6-renameex)."""
    try:
        from . import exercises as _ex
        wired = TYPE_NUM in _ex.TYPES and TYPE_NUM in _ex.GENERATORS
    except Exception:  # noqa: BLE001 — standalone load has no package
        wired = False
    state = ("registered in TYPES/GENERATORS — live"
             if wired else "designed; registration lands with the parent")
    return (f"<h3 id='status-b6-renameex'>{TYPE_NAME} exercise <small>(feature)</small></h3>"
            f"<p>Type {TYPE_NUM} ({BLOOM}): propose a better name for a weak "
            f"identifier; convention-checked plus rubric-justified. "
            f"<code>groundwork/renameex.py</code>. Status: {state}.</p>")
