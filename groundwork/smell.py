"""Name-that-smell exercises (F-2): identify the smell in a real snippet.

Exercise type 15 ("name-that-smell", Bloom analyse). Single-choice:
the learner reads a real snippet and names its dominant code smell.
Detectors are pure stdlib (ast + line scans); grading is exact
answer-text match — the same contract as types 7/16/18 — so no
sandbox runner is needed and the central grader needs no new logic.

Import-safe standalone: stdlib only, never imports groundwork, so
groundwork/exercises.py can import this module without a cycle.
Central wiring is lookups only: TYPES[15], GENERATORS[15], the
(7, 15, 16, 18) grade family, and a grading.py disclosure line.
"""
from __future__ import annotations

import ast
import html
import random

TYPE_NUM = 15
TYPE_NAME = "name-that-smell"
BLOOM = "analyse"

CODE_LIMIT = 800
LONG_FN_LINES = 20  # a function spanning more than this smells long
LONG_PARAMS = 5  # this many params (excl. self/cls) smells long
DEEP_NESTING = 4  # this many nested blocks smells deep
DUP_COPIES = 3  # this many identical lines smells duplicated
MAGIC_COUNT = 3  # this many distinct literals smells magic


def _tree(code: str):
    try:
        return ast.parse(code)
    except (SyntaxError, ValueError):
        return None


def _func_defs(tree):
    return [n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _det_long_function(code: str, tree) -> int:
    if tree is not None:
        fns = _func_defs(tree)
        if fns:
            span = max(getattr(n, "end_lineno", n.lineno) - n.lineno + 1
                       for n in fns)
            return max(0, span - LONG_FN_LINES)
    lines = [l for l in code.splitlines() if l.strip()]
    return max(0, len(lines) - LONG_FN_LINES)


def _det_long_params(code: str, tree) -> int:
    del code
    if tree is None:
        return 0
    best = 0
    for n in _func_defs(tree):
        params = [a.arg for a in n.args.args if a.arg not in ("self", "cls")]
        params += [a.arg for a in n.args.kwonlyargs]
        best = max(best, len(params))
    return max(0, best - LONG_PARAMS + 1)


def _depth(node, level: int) -> int:
    best = level
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While,
                              ast.With, ast.AsyncWith, ast.Try,
                              ast.ExceptHandler)):
            best = max(best, _depth(child, level + 1))
        else:
            best = max(best, _depth(child, level))
    return best


def _det_deep_nesting(code: str, tree) -> int:
    del code
    if tree is None:
        return 0
    return max(0, _depth(tree, 0) - DEEP_NESTING + 1)


def _det_duplicated(code: str, tree) -> int:
    del tree
    freq: dict[str, int] = {}
    for line in code.splitlines():
        s = line.strip()
        if len(s) >= 12 and not s.startswith(("#", '"""', "'''")):
            freq[s] = freq.get(s, 0) + 1
    return max(0, max(freq.values(), default=0) - DUP_COPIES + 1)


_MAGIC_OK = {0, 1, -1, 0.0, 1.0, True, False}


def _det_magic_numbers(code: str, tree) -> int:
    del code
    if tree is None:
        return 0
    vals = {n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant)
            and isinstance(n.value, (int, float))
            and n.value not in _MAGIC_OK}
    return max(0, len(vals) - MAGIC_COUNT + 1)


def _det_broad_except(code: str, tree) -> int:
    del code
    if tree is None:
        return 0
    n = 0
    for h in ast.walk(tree):
        if not isinstance(h, ast.ExceptHandler):
            continue
        if h.type is None:
            n += 1
        elif isinstance(h.type, ast.Name) and h.type.id in ("Exception",
                                                           "BaseException"):
            n += 1
    return n


SMELLS = (
    {"id": "long-function", "title": "Long Function",
     "blurb": "one function spans 20+ lines and does several jobs",
     "fix": "extract one helper per job",
     "detect": _det_long_function},
    {"id": "long-parameter-list", "title": "Long Parameter List",
     "blurb": "a function takes 5+ parameters",
     "fix": "bundle related params into one object",
     "detect": _det_long_params},
    {"id": "deep-nesting", "title": "Deep Nesting",
     "blurb": "blocks nest 4+ deep, hiding the happy path",
     "fix": "guard-clause or extract the inner block",
     "detect": _det_deep_nesting},
    {"id": "duplicated-code", "title": "Duplicated Code",
     "blurb": "the same long line appears 3+ times",
     "fix": "extract it once and call it",
     "detect": _det_duplicated},
    {"id": "magic-numbers", "title": "Magic Numbers",
     "blurb": "3+ unexplained numeric literals drive behavior",
     "fix": "name each constant where it is defined",
     "detect": _det_magic_numbers},
    {"id": "broad-except", "title": "Overly Broad Except",
     "blurb": "a bare or Exception-wide handler swallows every failure",
     "fix": "catch the narrowest error you can handle",
     "detect": _det_broad_except},
)

BY_ID = {e["id"]: e for e in SMELLS}


def _norm(text: str) -> str:
    return " ".join(str(text).strip().split())


def detect_all(code: str) -> dict:
    """Map smell id -> strength (0 means absent). Never raises."""
    tree = _tree(code or "")
    return {e["id"]: max(0, int(e["detect"](code or "", tree) or 0))
            for e in SMELLS}


def choose(code: str) -> tuple:
    """Strongest smell and its strength; ties break by catalog order."""
    scores = detect_all(code)
    order = [e["id"] for e in SMELLS]
    best = max(order, key=lambda sid: (scores[sid], -order.index(sid)))
    return BY_ID[best], scores[best]


def coerce_smell(value: str):
    """Match a ctx override to a catalog entry by id or title."""
    want = _norm(value).lower()
    for e in SMELLS:
        if want in (e["id"], e["title"].lower()):
            return e
    return None


def _code_from(concept, snippet, ctx: dict) -> str:
    return (ctx.get("runnable") or ctx.get("code_block")
            or "\n".join(snippet or []) or concept.name)


def generate(ex_id: str, concept, snippet, ctx: dict) -> dict:
    """Build a type-15 exercise; always returns a gradeable card.

    The dominant detected smell is the answer (grounded=True). A
    ctx["smell"] id/title forces the answer, mirroring the ctx["buggy"]
    override of spot-bug. When nothing fires, the card still renders
    with grounded=False so the pipeline skips it, like odd-one-out.
    """
    ctx = ctx or {}
    code = _code_from(concept, snippet, ctx)
    forced = coerce_smell(ctx.get("smell", ""))
    entry, strength = choose(code)
    if forced is not None:
        entry = forced
    grounded = forced is not None or strength > 0
    order = [e["id"] for e in SMELLS]
    scores = detect_all(code)
    others = sorted((e for e in SMELLS if e["id"] != entry["id"]),
                    key=lambda e: (-scores[e["id"]], order.index(e["id"])))
    choices = [entry["title"], others[0]["title"], others[1]["title"]]
    rng = random.Random(hash(ex_id) & 0xFFFFFFFF)
    rng.shuffle(choices)
    where = f"{concept.file}:{concept.line}" if concept.line else concept.file
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": concept.node_id,
        "concept": concept.name, "file": concept.file,
        "line": concept.line, "commit": ctx.get("commit", ""),
        "front": (f"Which code smell best describes this snippet from "
                  f"`{concept.name}`?\n```python\n{code[:CODE_LIMIT]}\n```"),
        "back": f"{entry['title']} — {entry['blurb']}. Fix: {entry['fix']}.",
        "payload": {"choices": choices, "answer": entry["title"],
                    "smell": entry["id"], "grounded": grounded,
                    "detail": entry["blurb"]},
        "hints": [f"Each choice names a structural habit — re-read the "
                  f"snippet for the loudest one.",
                  f"Look at {where}: `{concept.name}`.",
                  f"Worked step: the smell involves `{entry['title']}` "
                  f"({entry['blurb']}). Now say where."],
    }


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Exact answer-text match — same contract as types 7/16/18.

    Pure: runner is accepted and ignored, so review paths that always
    pass a sandbox keep working. Identical to the central family
    branch, so module and central verdicts never diverge.
    """
    del runner
    p = exercise.get("payload", {})
    want = _norm(p.get("answer", ""))
    ok = bool(want) and _norm(submission) == want
    return {"pass": ok, "score": 1.0 if ok else 0.0,
            "feedback": "Correct choice." if ok
            else f"Answer: {p.get('answer')}"}


def render(exercise: dict) -> str:
    """Single-choice radio form, mirroring the type-4 branch shape."""
    p = exercise.get("payload", {})
    front = html.escape(exercise.get("front", ""))
    opts = "".join(
        f'<label><input type="radio" name="answer" value="{html.escape(c)}"> '
        f'{html.escape(c)}</label><br>' for c in p.get("choices", []))
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (f"<article><h3>{html.escape(exercise.get('concept', ''))} "
            f"· {html.escape(exercise.get('type_name', TYPE_NAME))}</h3>"
            f"<p>{front}</p>"
            f"<form method='post'>{opts}<button>Submit</button></form>"
            f"{hints}"
            f"<p><small>{html.escape(exercise.get('file', ''))}:"
            f"{exercise.get('line', 0)}</small></p></article>")


def section_html(db_path: str = "") -> str:
    """Status subsection for the name-that-smell exercise type."""
    del db_path
    items = "".join(f"<li><b>{html.escape(e['title'])}</b> — "
                    f"{html.escape(e['blurb'])}; fix: "
                    f"{html.escape(e['fix'])}.</li>" for e in SMELLS)
    return ("<h3 id='status-b6-smell'>Name-that-smell <small>(feature)</small></h3>"
            "<p>Type 15 exercise: read a real snippet and name its dominant "
            "smell — six stdlib-detected smells, one choice, machine-graded "
            "with no sandbox. <code>groundwork/smell.py</code>.</p>"
            f"<ul>{items}</ul>")
