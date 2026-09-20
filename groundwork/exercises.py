"""Exercise engine: MVP types as plugins with generate/render/grade.

Every exercise: {id, type, concept_id, bloom, front, back, payload,
hints: [nudge, pointer, worked], commit, file, line}.
Machine-graded except explain-* (rubric checklist offline).
Choice types (7, 16, 18) carry payload {choices, answer}; the order
type (10) carries {lines, solution} like Parsons.
"""
from __future__ import annotations

import ast
import html
import random
import re
from pathlib import Path

from . import diretro as diretromod
from . import docdoctest as docdoctestmod
from . import errbranch as errbranchmod
from . import golf as golfmod
from . import logretro as logretromod
from . import renameex as renameexmod
from . import smell as smellmod
from . import typeanno as typeannomod

# type number -> (name, bloom)
TYPES = {
    1: ("flashcard", "recall"),
    2: ("cloze", "recall"),
    3: ("signature-recall", "recall"),
    4: ("where-live", "recall"),
    5: ("explain-words", "explain"),
    6: ("explain-diff", "explain"),
    7: ("design-rationale", "explain"),
    8: ("predict-output", "apply"),
    9: ("trace-variable", "apply"),
    10: ("call-path-trace", "apply"),
    11: ("parsons", "apply"),
    12: ("complete-function", "apply"),
    13: ("spot-bug", "analyse"),
    14: ("fix-bug", "analyse"),
    15: ("name-that-smell", "analyse"),
    16: ("blast-radius", "analyse"),
    17: ("rename-symbol", "analyse"),
    18: ("odd-one-out", "analyse"),
    19: ("refactor-under-test", "modify"),
    20: ("extend-feature", "modify"),
    21: ("code-review", "evaluate"),
    22: ("compare-implementations", "evaluate"),
    23: ("rebuild-from-spec", "create"),
    24: ("teach-it-back", "create"),
    25: ("write-docstring", "explain"),
    26: ("complexity-golf", "analyse"),
    27: ("dependency-injection", "modify"),
    28: ("error-branch", "analyse"),
    29: ("logging-retrofit", "analyse"),
    30: ("match-pairs", "recall"),
    31: ("type-annotation", "apply"),
    32: ("doc-example", "apply"),
}

BLOOM_TYPES = {
    "recall": [1, 2, 3, 4],
    "explain": [5, 6, 7, 25, 1],
    "apply": [8, 10, 11, 12, 9, 31, 32],
    "analyse": [13, 14, 15, 16, 17, 18, 9, 26, 28, 29],
    "modify": [12, 14, 19, 20, 27],
    "evaluate": [21, 22],
    "create": [24, 23],
}


def get_snippet(repo: str | Path, file: str, line: int, context: int = 15) -> list[str]:
    p = Path(repo) / file
    if not p.is_file() and Path(file).is_file():
        p = Path(file)
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    start = max(0, line - context - 1)
    return lines[start:line + context]


def _norm(code: str) -> str:
    return " ".join(code.strip().split())


def _ast_norm(code: str) -> str | None:
    try:
        return ast.dump(ast.parse(code))
    except SyntaxError:
        return None


def _parse_keyed(submission: str) -> dict:
    """Parse `id=value` lines (one per line) into {id: value}."""
    out: dict = {}
    for line in str(submission).splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            try:
                out[int(k)] = v.strip()
            except ValueError:
                out[k] = v.strip()
    return out


def _hints(question: str, answer: str, snippet: list[str],
           file: str = "", line: int = 0) -> list[str]:
    if snippet and file:
        where = f"{file}:{line}" if line else file
        pointer = f"Look at {where}: `{snippet[0].strip()}`"
    elif snippet:
        pointer = f"Re-read this snippet: `{snippet[0].strip()}`"
    else:
        pointer = "Re-read the linked file."
    return [f"Recall what {question} is for before answering.",
            pointer,
            f"Worked step: the answer involves `{answer[:80]}`. Now say why."]


def _base(ex_id: str, num: int, concept, snippet, commit: str) -> dict:
    name, bloom = TYPES[num]
    return {
        "id": ex_id, "type": num, "type_name": name, "bloom": bloom,
        "concept_id": concept.node_id, "concept": concept.name,
        "file": concept.file, "line": concept.line, "commit": commit,
        "hints": _hints(concept.name, concept.name, snippet,
                      concept.file, concept.line),
    }


# ------------------------------------------------------------- generators

def gen_flashcard(ex_id, concept, snippet, ctx) -> dict:
    ex = _base(ex_id, 1, concept, snippet, ctx.get("commit", ""))
    q = f"What does `{concept.name}` do, and where is it defined?"
    a = f"`{concept.name}` ({concept.kind}) in {concept.file}:{concept.line}."
    ex.update(front=q, back=a, payload={"question": q, "answer": a})
    return ex


_CLOZE_STOP = {"def", "return", "if", "else", "elif", "for", "while", "in",
               "import", "from", "None", "True", "False", "self", "print",
               "assert", "with", "as", "class", "pass", "and", "or", "not",
               "is", "raise", "try", "except", "finally", "lambda", "await"}


def gen_cloze(ex_id, concept, snippet, ctx) -> dict:
    ex = _base(ex_id, 2, concept, snippet, ctx.get("commit", ""))
    text = "\n".join(snippet) or concept.name
    freq: dict[str, int] = {}
    for w in re.findall(r"[A-Za-z_]\w*", text):
        if len(w) >= 2 and w not in _CLOZE_STOP:
            freq[w] = freq.get(w, 0) + 1
    names = [concept.name] + [w for w, _ in
                              sorted(freq.items(), key=lambda kv: -kv[1])
                              if w != concept.name]
    blanks = []
    template = text
    for i, name in enumerate(names[:3]):
        if name not in template:
            continue
        template = template.replace(name, f"___({i})")
        blanks.append({"id": i, "answers": [name]})
    if not blanks:
        blanks = [{"id": 0, "answers": [concept.name]}]
        template = concept.name.replace(concept.name, "___(0)")
    ex.update(
        front=f"Fill in the blanks:\n```\n{template.strip()}\n```",
        back=text.strip(),
        payload={"template": template.strip(), "blanks": blanks,
                 "answers": [b["answers"][0] for b in blanks]})
    return ex


def _signature_distractors(sig: str) -> list[str]:
    """Plausible wrong signatures (reordered/dropped params)."""
    out = [sig]
    try:
        tree = ast.parse(sig if sig.strip().startswith("def") else f"def {sig}: ...")
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
        params = [a.arg for a in fn.args.args]
        if len(params) >= 2:
            swapped = params[:]
            swapped[0], swapped[1] = swapped[1], swapped[0]
            out.append(f"{fn.name}({', '.join(swapped)})")
        if params:
            out.append(f"{fn.name}({', '.join(params[1:] or ['...'])})")
    except (SyntaxError, StopIteration):
        out.append(sig + "  # or does it take no arguments?")
    seen, choices = set(), []
    for c in out:
        if c not in seen:
            seen.add(c)
            choices.append(c)
    return choices[:3]


def gen_signature(ex_id, concept, snippet, ctx) -> dict:
    ex = _base(ex_id, 3, concept, snippet, ctx.get("commit", ""))
    sig = next((l.strip() for l in snippet
                if "def " + concept.name in l or concept.name + "(" in l),
               f"{concept.name}(...)")
    choices = _signature_distractors(sig)
    rng = random.Random(hash(ex_id) & 0xFFFFFFFF)
    rng.shuffle(choices)
    ex.update(
        front=f"Write the full signature of `{concept.name}` (params + return).",
        back=sig,
        payload={"func": concept.name, "signature": sig,
                 "choices": choices, "answer": sig})
    return ex


def gen_where_live(ex_id, concept, snippet, ctx) -> dict:
    ex = _base(ex_id, 4, concept, snippet, ctx.get("commit", ""))
    graph = ctx.get("graph")
    files = sorted({n.file for n in graph.nodes.values()}) if graph else [concept.file]
    choices = [concept.file] + [f for f in files if f != concept.file][:3]
    rng = random.Random(hash(ex_id) & 0xFFFFFFFF)
    rng.shuffle(choices)
    ex.update(
        front=f"Which file owns `{concept.name}`?",
        back=concept.file,
        payload={"choices": choices, "answer": concept.file})
    return ex


def gen_explain_words(ex_id, concept, snippet, ctx) -> dict:
    ex = _base(ex_id, 5, concept, snippet, ctx.get("commit", ""))
    code = "\n".join(snippet)
    rubric = [concept.name, concept.kind, concept.file.split("/")[-1]]
    decisions = [d for d in ctx.get("decisions", [])
                 if d.get("symbol") in (concept.name, concept.node_id)]
    if decisions:
        rubric += [decisions[0].get("chosen", ""), decisions[0].get("reason", "")[:40]]
    rubric = [r for r in rubric if r]
    ex.update(
        front=f"In your own words: what does `{concept.name}` do and why is it shaped this way?\n```\n{code[:800]}\n```",
        back="; ".join(rubric),
        payload={"rubric": rubric, "code": code[:800]})
    return ex


def gen_explain_diff(ex_id, concept, snippet, ctx) -> dict:
    ex = _base(ex_id, 6, concept, snippet, ctx.get("commit", ""))
    excerpt = "\n".join(ctx.get("diff_lines", [])[:30]) or "\n".join(snippet)
    rubric = [concept.name, concept.file, "changed", "because"]
    ex.update(
        front=f"What did the latest change to `{concept.name}` alter?\n```diff\n{excerpt[:800]}\n```",
        back=f"The change touched {concept.file} around line {concept.line}.",
        payload={"rubric": rubric, "diff": excerpt[:800]})
    return ex


def _callers_of(graph, node_id: str, name: str = "") -> list[str]:
    """Edge sources calling into node_id.

    Mirrors lesson_for: edge endpoints may be bare names, so match
    either the node id or the display name.
    """
    if graph is None:
        return []
    return sorted({s for s, d, k in graph.edges
                   if d in (node_id, name) and k == "calls"
                   and s != node_id})


def _callees_of(graph, node_id: str, name: str = "") -> list[str]:
    """Edge targets node_id calls, falling back to the node's calls list."""
    if graph is None:
        return []
    out = sorted({d for s, d, k in graph.edges
                  if s == node_id and k == "calls" and d != node_id})
    if not out:
        node = graph.nodes.get(node_id)
        out = [c for c in (getattr(node, "calls", []) or [])
               if c != node_id and c != name]
    return out


def _disp(graph, node_id: str) -> str:
    node = graph.nodes.get(node_id) if graph is not None else None
    if node is not None and node.name:
        return node.name
    return node_id


def _decision_for(ctx: dict, concept) -> dict | None:
    for d in ctx.get("decisions", []):
        if d.get("symbol") in (concept.name, concept.node_id):
            if d.get("chosen"):
                return d
    return None


def gen_design_rationale(ex_id, concept, snippet, ctx) -> dict:
    """Why this approach beat the alternative — from the decision log."""
    ex = _base(ex_id, 7, concept, snippet, ctx.get("commit", ""))
    d = _decision_for(ctx, concept)
    rng = random.Random(hash(ex_id) & 0xFFFFFFFF)
    if d is None:
        choices = ["A rationale was recorded", "No rationale was recorded"]
        ex.update(
            front=f"Was a design rationale recorded for `{concept.name}`?",
            back="No rationale was recorded for this symbol.",
            payload={"choices": choices, "answer": "No rationale was recorded",
                     "grounded": False})
        return ex
    choices = [d["chosen"], d.get("rejected", "another approach")]
    rng.shuffle(choices)
    ex.update(
        front=f"Why is `{concept.name}` built this way — what beat what?",
        back=f"Chose {d['chosen']} over {d.get('rejected', '?')}: {d.get('reason', '')}",
        payload={"choices": choices, "answer": d["chosen"],
                 "reason": d.get("reason", ""), "grounded": True})
    return ex


def _predict_distractors(expected: str) -> list[str]:
    """Plausible wrong outputs so prediction can start as recognition."""
    exp = expected.strip()
    out = [exp]
    if re.fullmatch(r"-?\d+", exp):
        out += [str(int(exp) + 1), str(int(exp) - 1)]
    elif re.fullmatch(r"-?\d+\.\d+", exp):
        out += [str(float(exp) + 1.0), str(float(exp) * 10)]
    else:
        out += ["An error is raised", "No output"]
    seen, choices = set(), []
    for c in out:
        if c not in seen:
            seen.add(c)
            choices.append(c)
    return choices[:3]


def gen_predict_output(ex_id, concept, snippet, ctx) -> dict:
    ex = _base(ex_id, 8, concept, snippet, ctx.get("commit", ""))
    code = ctx.get("runnable") or "\n".join(snippet)
    expected = ctx.get("expected_output", "")
    choices = _predict_distractors(expected)
    rng = random.Random(hash(ex_id) & 0xFFFFFFFF)
    rng.shuffle(choices)
    ex.update(
        front=f"Predict the stdout/return value of:\n```python\n{code[:600]}\n```",
        back=expected,
        payload={"code": code, "expected": expected,
                 "choices": choices, "answer": expected})
    return ex


def gen_trace_variable(ex_id, concept, snippet, ctx) -> dict:
    ex = _base(ex_id, 9, concept, snippet, ctx.get("commit", ""))
    code = ctx.get("runnable") or "x = 1\nx = x + 2\nx = x * 3"
    var = ctx.get("trace_var", "x")
    expected = ctx.get("trace_expected", [])
    ex.update(
        front=f"Fill the value of `{var}` after each line:\n```python\n{code[:600]}\n```",
        back=str(expected),
        payload={"code": code, "var": var, "expected": expected})
    return ex


def _call_chain(graph, concept) -> list[str]:
    """Entry → concept → effect display names; [concept] when isolated."""
    if graph is None:
        return [concept.name]
    callers = [_disp(graph, n) for n in _callers_of(graph, concept.node_id, concept.name)]
    callees = [_disp(graph, n) for n in _callees_of(graph, concept.node_id, concept.name)]
    callers = [c for c in dict.fromkeys(callers) if c != concept.name]
    callees = [c for c in dict.fromkeys(callees) if c != concept.name]
    if callers and callees:
        chain = [callers[0], concept.name, callees[0]]
    elif callers:
        chain = [callers[0], concept.name]
    elif callees:
        chain = [concept.name, callees[0]]
    else:
        chain = [concept.name]
    if len(chain) < 2 or len(set(chain)) != len(chain):
        return [concept.name]
    return chain


def gen_call_path(ex_id, concept, snippet, ctx) -> dict:
    """Order the calls from entry point to effect through this concept."""
    ex = _base(ex_id, 10, concept, snippet, ctx.get("commit", ""))
    chain = _call_chain(ctx.get("graph"), concept)
    order = list(range(len(chain)))
    rng = random.Random(hash(ex_id) & 0xFFFFFFFF)
    shuffled = order[:]
    rng.shuffle(shuffled)
    ex.update(
        front=f"Order the calls from entry point to effect through `{concept.name}`.",
        back=" → ".join(chain),
        payload={"lines": [chain[i] for i in shuffled],
                 "solution": chain,
                 "grounded": len(chain) >= 2})
    return ex


def gen_parsons(ex_id, concept, snippet, ctx) -> dict:
    ex = _base(ex_id, 11, concept, snippet, ctx.get("commit", ""))
    block = ctx.get("runnable") or ctx.get("code_block") or "\n".join(snippet)
    lines = [l for l in block.splitlines() if l.strip()][:8] or [f"{concept.name}()"]
    order = list(range(len(lines)))
    rng = random.Random(hash(ex_id) & 0xFFFFFFFF)
    shuffled = order[:]
    rng.shuffle(shuffled)
    tests = ctx.get("tests", "")
    ex.update(
        front="Reorder these lines into working code.",
        back="\n".join(lines),
        payload={"lines": [lines[i] for i in shuffled],
                 "solution": lines, "tests": tests,
                 "code_block": block})
    return ex


def gen_complete_function(ex_id, concept, snippet, ctx) -> dict:
    ex = _base(ex_id, 12, concept, snippet, ctx.get("commit", ""))
    body = ctx.get("runnable") or "\n".join(snippet) or "pass"
    tests = ctx.get("tests", "")
    stub_lines = [l for l in body.splitlines()]
    stub = "\n".join(stub_lines[:1] + ["    # TODO: implement", "    pass"])
    ex.update(
        front=f"Implement the body of `{concept.name}` so the hidden tests pass.\n```python\n{stub}\n```",
        back=body,
        payload={"stub": stub, "tests": tests, "reference": body})
    return ex


def gen_spot_bug(ex_id, concept, snippet, ctx) -> dict:
    ex = _base(ex_id, 13, concept, snippet, ctx.get("commit", ""))
    lines = (ctx.get("buggy") or "\n".join(snippet)).splitlines() or [""]
    bug_line = ctx.get("bug_line", min(2, len(lines)))
    numbered = "\n".join(f"{i + 1}: {l}" for i, l in enumerate(lines))
    ex.update(
        front=f"Which line contains the injected defect?\n```\n{numbered[:800]}\n```",
        back=str(bug_line),
        payload={"snippet": numbered[:800], "bug_line": bug_line})
    return ex


def gen_fix_bug(ex_id, concept, snippet, ctx) -> dict:
    ex = _base(ex_id, 14, concept, snippet, ctx.get("commit", ""))
    buggy = ctx.get("buggy") or "\n".join(snippet)
    tests = ctx.get("tests", "")
    ex.update(
        front=f"Make the failing tests pass (bug in `{concept.name}`):\n```python\n{buggy[:600]}\n```",
        back=ctx.get("fixed", ""),
        payload={"buggy": buggy, "fixed": ctx.get("fixed", ""),
                 "tests": tests})
    return ex


def gen_blast_radius(ex_id, concept, snippet, ctx) -> dict:
    """Predict what breaks if this concept changes — graph impact."""
    ex = _base(ex_id, 16, concept, snippet, ctx.get("commit", ""))
    graph = ctx.get("graph")
    files = sorted({n.file for n in graph.nodes.values()}) if graph else []
    callers = ([_disp(graph, n) for n in _callers_of(graph, concept.node_id, concept.name)]
               if graph else [])
    callers = [c for c in dict.fromkeys(callers) if c != concept.name]
    rng = random.Random(hash(ex_id) & 0xFFFFFFFF)
    if callers:
        answer = callers[0]
        pool = callers[1:] + [concept.file] + [f for f in files
                                               if f != concept.file]
        front = (f"If `{concept.name}` changes signature, "
                 f"which of these breaks first?")
        back = f"`{answer}` calls `{concept.name}`, so it breaks first."
    else:
        answer = concept.file
        pool = [f for f in files if f != concept.file] + ["another module"]
        front = (f"If `{concept.name}` changes, "
                 f"which file must be re-checked first?")
        back = f"`{concept.name}` lives in {concept.file}."
    choices = [answer] + [x for x in pool if x != answer][:2]
    rng.shuffle(choices)
    ex.update(front=front, back=back,
              payload={"choices": choices, "answer": answer,
                       "grounded": True})
    return ex


def gen_odd_one_out(ex_id, concept, snippet, ctx) -> dict:
    """Find the symbol with no call relationship to this concept."""
    ex = _base(ex_id, 18, concept, snippet, ctx.get("commit", ""))
    graph = ctx.get("graph")
    rng = random.Random(hash(ex_id) & 0xFFFFFFFF)
    related, outsider, grounded = [], None, False
    if graph is not None:
        rel_ids = set(_callers_of(graph, concept.node_id, concept.name))
        rel_ids |= set(_callees_of(graph, concept.node_id, concept.name))
        related = [_disp(graph, n) for n in sorted(rel_ids)]
        related = [r for r in dict.fromkeys(related) if r != concept.name]
        rel_set = set(related) | {concept.name}
        for nid in sorted(graph.nodes):
            name = _disp(graph, nid)
            if name not in rel_set and nid != concept.node_id:
                outsider = name
                break
        grounded = len(related) >= 2 and outsider is not None
    if grounded:
        choices = related[:2] + [outsider]
        answer = outsider
        front = (f"Two of these work directly with `{concept.name}`. "
                 f"Which one does not?")
        back = f"`{answer}` has no call relationship with `{concept.name}`."
    else:
        choices = [concept.name, concept.file, concept.kind]
        answer = concept.kind
        front = ("Which of these is not the name of something "
                 f"you studied in `{concept.file}`?")
        back = f"`{concept.kind}` is a kind label, not a symbol name."
    rng.shuffle(choices)
    ex.update(front=front, back=back,
              payload={"choices": choices, "answer": answer,
                       "grounded": grounded})
    return ex


def gen_refactor(ex_id, concept, snippet, ctx) -> dict:
    """Refactor for clarity without changing behavior; tests stay green."""
    ex = _base(ex_id, 19, concept, snippet, ctx.get("commit", ""))
    body = ctx.get("runnable") or "\n".join(snippet) or "pass"
    tests = ctx.get("tests", "")
    ex.update(
        front=f"Refactor `{concept.name}` — clearer, simpler, or faster — "
        f"without changing what it does. Hidden tests must stay green.\n"
        f"```python\n{body[:600]}\n```",
        back=body,
        payload={"original": body, "tests": tests, "reference": body,
                 "grounded": bool(tests)})
    return ex


def gen_rebuild(ex_id, concept, snippet, ctx) -> dict:
    """Write a mini version from the spec alone; hidden tests judge it."""
    ex = _base(ex_id, 23, concept, snippet, ctx.get("commit", ""))
    body = ctx.get("runnable") or "\n".join(snippet) or "pass"
    tests = ctx.get("tests", "")
    lesson = ctx.get("lesson", {}) or {}
    spec = lesson.get("summary") or f"Reimplement `{concept.name}`."
    sig = next((l for l in body.splitlines() if l.strip()), concept.name)
    ex.update(
        front=f"Rebuild `{concept.name}` from this spec alone — no peeking "
        f"at the original:\n{spec}\nKeep this interface:\n```python\n{sig}\n```",
        back=body,
        payload={"spec": spec, "signature": sig, "tests": tests,
                 "reference": body, "grounded": bool(tests)})
    return ex


def gen_extend(ex_id, concept, snippet, ctx) -> dict:
    """Add a small optional parameter; old behavior must keep working."""
    ex = _base(ex_id, 20, concept, snippet, ctx.get("commit", ""))
    body = ctx.get("runnable") or "\n".join(snippet) or "pass"
    tests = ctx.get("tests", "")
    param = "strict"
    ex.update(
        front=f"Extend `{concept.name}` with an optional parameter "
        f"`{param}=False` (it may change behavior only when True). "
        f"All existing behavior must keep working.\n```python\n{body[:600]}\n```",
        back=body,
        payload={"param": param, "tests": tests, "reference": body,
                 "grounded": bool(tests)})
    return ex


def gen_code_review(ex_id, concept, snippet, ctx) -> dict:
    """Review a plausible-but-flawed version: name the bad line and why."""
    ex = _base(ex_id, 21, concept, snippet, ctx.get("commit", ""))
    buggy = ctx.get("buggy", "")
    bug_line = ctx.get("bug_line", 0)
    if buggy and bug_line:
        numbered = "\n".join(f"{i + 1}: {l}"
                             for i, l in enumerate(buggy.splitlines()))
        rubric = [concept.name, str(bug_line)]
        ex.update(
            front=f"Review this version of `{concept.name}` like a maintainer: "
            f"which line is wrong, and what goes wrong because of it?\n"
            f"```python\n{numbered[:800]}\n```",
            back=f"Line {bug_line} is the defect.",
            payload={"snippet": numbered[:800], "bug_line": bug_line,
                     "rubric": rubric, "grounded": True})
        return ex
    code = "\n".join(snippet) or concept.name
    ex.update(
        front=f"Review `{concept.name}` like a maintainer: which line is "
        f"the riskiest, and what could go wrong there?\n```\n{code[:800]}\n```",
        back=f"No seeded flaw here — any reasoned risk counts.",
        payload={"snippet": code[:800], "bug_line": 0,
                 "rubric": [concept.name, concept.file],
                 "grounded": False})
    return ex


def gen_compare(ex_id, concept, snippet, ctx) -> dict:
    """Choose the correct implementation and justify the choice."""
    ex = _base(ex_id, 22, concept, snippet, ctx.get("commit", ""))
    ref = ctx.get("fixed") or ctx.get("runnable") or "\n".join(snippet)
    buggy = ctx.get("buggy", "")
    rng = random.Random(hash(ex_id) & 0xFFFFFFFF)
    if buggy and ref.strip() != buggy.strip():
        opts = [(ref, True), (buggy, False)]
        rng.shuffle(opts)
        labels = "AB"
        shown = [(f"Version {labels[i]}", code, ok)
                 for i, (code, ok) in enumerate(opts)]
        answer = next(l for l, _, ok in
                      [(labels[i], c, ok) for i, (c, ok) in enumerate(opts)]
                      if ok)
        body = "\n\n".join(f"**{l}:**\n```python\n{c[:500]}\n```"
                           for l, c, _ in shown)
        rubric = [concept.name]
        grounded = True
    else:
        stub = "pass  # TODO: not implemented"
        answer = "A"
        body = (f"**Version A:**\n```python\n{ref[:500]}\n```\n\n"
                f"**Version B:**\n```python\n{stub}\n```")
        rubric = [concept.name]
        grounded = False
    ex.update(
        front=f"Two versions of `{concept.name}`. First line of your answer: "
        f"A or B (the correct one). Then justify it.\n{body}",
        back=f"Version {answer} is correct.",
        payload={"answer": answer, "rubric": rubric, "grounded": grounded})
    return ex


def gen_teach_back(ex_id, concept, snippet, ctx) -> dict:
    """Explain it for a newcomer, then answer the novice's follow-ups."""
    ex = _base(ex_id, 24, concept, snippet, ctx.get("commit", ""))
    code = "\n".join(snippet)
    rubric = [concept.name, concept.kind, concept.file.split("/")[-1]]
    graph = ctx.get("graph")
    if graph is not None:
        rel = ([_disp(graph, n)
                for n in _callers_of(graph, concept.node_id, concept.name)]
               + [_disp(graph, n)
                  for n in _callees_of(graph, concept.node_id, concept.name)])
        rel = [r for r in dict.fromkeys(rel) if r != concept.name][:2]
        rubric += rel
    rubric = [r for r in rubric if r]
    followups = [
        f"What does `{concept.name}` do when it is called?",
        f"Why does `{concept.name}` exist — what breaks without it?",
    ]
    ex.update(
        front=f"Teach `{concept.name}` back to a newcomer in your own words, "
        f"then answer their follow-ups:\n```\n{code[:600]}\n```\n"
        + "\n".join(f"{i + 1}. {q}" for i, q in enumerate(followups)),
        back="; ".join(rubric),
        payload={"rubric": rubric, "followups": followups})
    return ex


def gen_docstring(ex_id, concept, snippet, ctx) -> dict:
    """Write the docstring from signature alone; rubric-graded."""
    ex = _base(ex_id, 25, concept, snippet, ctx.get("commit", ""))
    code = "\n".join(snippet)
    params: list[str] = []
    fn = None
    try:
        tree = ast.parse(code)
        # The window starts above the concept: match the def by name,
        # never the first def in the window.
        fns = [n for n in ast.walk(tree)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name == concept.name]
        fn = fns[0] if fns else None
        if fn is not None:
            params = [a.arg for a in fn.args.args
                      if a.arg not in ("self", "cls")]
            params += [a.arg for a in fn.args.kwonlyargs]
    except SyntaxError:
        fn = None
    if fn is not None:
        wlines = code.splitlines()
        sig = wlines[fn.lineno - 1].strip() if 0 < fn.lineno <= len(wlines) else concept.name
    else:
        sig = next((l for l in code.splitlines() if l.strip()), concept.name)
    rubric = [concept.name] + params
    if "return" in code:
        rubric.append("return")
    rubric = [r for r in dict.fromkeys(rubric) if r]
    ex.update(
        front=f"Write the docstring for `{concept.name}` from its signature "
        f"alone — purpose, parameters, what it returns.\n```python\n{sig}\n```",
        back=f"Documented: {', '.join(rubric) or concept.name}.",
        payload={"rubric": rubric, "signature": sig,
                 "grounded": fn is not None})
    return ex


def gen_match(ex_id, concept, snippet, ctx) -> dict:
    """Match-up across the module's concepts: name -> file it lives in.

    Recognition before recall: cheaper than where-live per item, and the
    whole set is reviewed in one go.
    """
    pairs = ctx.get("match_pairs", [])[:6]
    if len(pairs) < 2:
        pairs = [[concept.name, concept.file]]
    left = [a for a, _ in pairs]
    rng = random.Random(hash(ex_id) & 0xFFFFFFFF)
    order = list(range(len(left)))
    rng.shuffle(order)
    left_shown = [left[i] for i in order]
    right = sorted({b for _, b in pairs})
    key = {}
    for i, a in enumerate(left_shown):
        b = next(bb for aa, bb in pairs if aa == a)
        key[i] = chr(ord("A") + right.index(b))
    ex = _base(ex_id, 30, concept, snippet, ctx.get("commit", ""))
    ex.update(
        front="Match each item on the left to its partner on the right.",
        back="; ".join(f"{a} → {b}" for a, b in pairs),
        payload={"pairs": pairs, "left": left_shown, "right": right,
                 "key": {str(k): v for k, v in key.items()}})
    return ex


GENERATORS = {
    1: gen_flashcard, 2: gen_cloze, 3: gen_signature, 4: gen_where_live,
    5: gen_explain_words, 6: gen_explain_diff, 7: gen_design_rationale,
    8: gen_predict_output, 9: gen_trace_variable, 10: gen_call_path,
    11: gen_parsons, 12: gen_complete_function, 13: gen_spot_bug,
    14: gen_fix_bug, 15: smellmod.generate,
    16: gen_blast_radius, 17: renameexmod.generate, 18: gen_odd_one_out,
    19: gen_refactor, 20: gen_extend, 21: gen_code_review,
    22: gen_compare, 23: gen_rebuild, 24: gen_teach_back, 25: gen_docstring,
    26: golfmod.generate, 27: diretromod.generate, 28: errbranchmod.generate,
    29: logretromod.generate, 30: gen_match,
    31: typeannomod.generate, 32: docdoctestmod.generate,
}


def generate(type_num: int, ex_id: str, concept, snippet: list[str], ctx: dict) -> dict:
    try:
        return GENERATORS[type_num](ex_id, concept, snippet, ctx)
    except KeyError:
        raise ValueError(f"unknown exercise type {type_num}")


# ----------------------------------------------------------------- grading

def _has_default_param(fn, param: str) -> bool:
    """True when fn defines param with a default value (i.e. optional)."""
    positional = list(fn.args.args)
    defaults = list(fn.args.defaults or [])
    if defaults:
        for arg, default in zip(positional[len(positional) - len(defaults):],
                                defaults):
            if arg.arg == param and default is not None:
                return True
    for arg, default in zip(fn.args.kwonlyargs, fn.args.kw_defaults or []):
        if arg.arg == param and default is not None:
            return True
    return False


def _grade_order(p: dict, submission: str) -> dict:
    """Grade an order-the-items answer against payload {lines, solution}.

    No sandbox needed: the reference order itself is ground truth.
    """
    try:
        idx = [int(x) for x in submission.replace(",", " ").split()]
        ordered = [p["lines"][i] for i in idx]
    except (ValueError, IndexError, KeyError, TypeError):
        return {"pass": False, "score": 0.0,
                "feedback": "Submit space-separated item indices."}
    solution = p.get("solution", [])
    if ordered == solution:
        return {"pass": True, "score": 1.0, "feedback": "Correct order."}
    bad = [str(i + 1) for i, (a, b) in enumerate(zip(ordered, solution))
           if a != b]
    if len(ordered) != len(solution):
        bad.append(f"length {len(ordered)}≠{len(solution)}")
    right = max(0, len(solution) - len([b for b in bad if b.isdigit()]))
    return {"pass": False, "score": right / max(1, len(solution)),
            "feedback": f"Positions {', '.join(bad)} wrong "
                        f"({right}/{len(solution)} right). Reorder and retry."}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Grade a submission -> {pass: bool, score: float, feedback: str}."""
    t = exercise["type"]
    p = exercise.get("payload", {})
    if t == 1:  # self-rating 0-5
        try:
            r = int(str(submission).strip())
        except ValueError:
            return {"pass": False, "score": 0.0,
                    "feedback": "Rate your recall 0-5."}
        return {"pass": r >= 3, "score": r / 5.0,
                "feedback": "Logged." if r >= 3 else "Review the back, then retry."}
    if t == 2:
        blanks = p.get("blanks") or [{"id": 0, "answers": p.get("answers", [""])}]
        given = _parse_keyed(submission)
        if not given and len(blanks) == 1:
            given = {blanks[0]["id"]: submission.strip()}
        wrong = []
        for b in blanks:
            ans = given.get(b["id"], given.get(str(b["id"]), ""))
            candidates = [_norm(a) for a in b.get("answers", [])]
            hit = _norm(ans) in candidates
            if not hit:
                an = _ast_norm(ans)
                hit = any(an is not None and an == _ast_norm(a)
                          for a in b.get("answers", []))
            if not hit:
                wrong.append(b["id"])
        ok = not wrong
        score = (len(blanks) - len(wrong)) / max(1, len(blanks))
        return {"pass": ok, "score": score,
                "feedback": "All blanks correct." if ok else
                f"Blank(s) {wrong} wrong — re-read the snippet."}
    if t == 3:
        ok = _norm(submission) == _norm(p.get("signature", ""))
        if not ok:
            an, bn = _ast_norm("def " + submission.strip() + ":\n pass"), None
            try:
                bn = _ast_norm("def " + p.get("signature", "").strip() + ":\n pass")
            except Exception:
                bn = None
            ok = an is not None and an == bn
        return {"pass": ok, "score": 1.0 if ok else 0.0,
                "feedback": "Signature matches." if ok else f"Expected: {p.get('signature')}"}
    if t == 4:
        ok = submission.strip() == p.get("answer")
        return {"pass": ok, "score": 1.0 if ok else 0.0,
                "feedback": "Correct file." if ok else f"It lives in {p.get('answer')}"}
    if t in (7, 16, 18):  # single-choice from {choices}, exact answer text
        want = _norm(p.get("answer", ""))
        ok = bool(want) and _norm(submission) == want
        return {"pass": ok, "score": 1.0 if ok else 0.0,
                "feedback": "Correct choice." if ok else f"Answer: {p.get('answer')}"}
    if t == 10:
        return _grade_order(p, submission)
    if t in (5, 6, 25):
        text = submission.lower()
        hits = [r for r in p.get("rubric", []) if r and r.lower() in text]
        total = max(1, len(p.get("rubric", [])))
        score = len(hits) / total
        return {"pass": score >= 0.5, "score": score,
                "feedback": f"Covered {len(hits)}/{total} key points." +
                ("" if score >= 0.5 else f" Missing: {', '.join(r for r in p.get('rubric', []) if r.lower() not in text)[:120]}")}
    if t in (21, 24):  # rubric checklist; reviews also name the bad line
        text = submission.lower()
        hits = [r for r in p.get("rubric", []) if r and r.lower() in text]
        total = max(1, len(p.get("rubric", [])))
        score = len(hits) / total
        if t == 21 and p.get("bug_line"):
            accused = None
            for tok in re.findall(r"-?\d+", submission):
                accused = int(tok)
                break
            line_ok = accused == p["bug_line"]
        else:
            line_ok = True
        ok = line_ok and score >= 0.5
        detail = f"Covered {len(hits)}/{total} key points."
        if t == 21 and p.get("bug_line") and accused != p["bug_line"]:
            detail += f" The defect is on line {p['bug_line']}."
        return {"pass": ok, "score": score, "feedback": detail}
    if t == 22:  # first letter picks the version; reasons stay on record
        letter = next((ch for ch in str(submission).strip().upper()
                       if ch.isalpha()), "")
        ok = bool(letter) and letter == str(p.get("answer", "")).upper()
        return {"pass": ok, "score": 1.0 if ok else 0.0,
                "feedback": "Correct version." if ok else
                f"Version {p.get('answer')} is the correct one."}
    if t == 13:
        try:
            ok = int(str(submission).strip()) == int(p.get("bug_line"))
        except ValueError:
            ok = False
        return {"pass": ok, "score": 1.0 if ok else 0.0,
                "feedback": "Found it." if ok else "Not that line — re-read the snippet."}
    if t == 30:
        pairs = p.get("pairs", [])
        left = p.get("left", [a for a, _ in pairs])
        right = p.get("right", sorted({b for _, b in pairs}))
        given = {int(k) if str(k).isdigit() else k: str(v).strip().upper()
                 for k, v in _parse_keyed(submission).items()}
        if not given and len(left) == 1:
            given = {0: str(submission).strip().upper()}
        wrong = []
        for i, a in enumerate(left):
            want = next((b for aa, b in pairs if aa == a), None)
            want_letter = chr(ord("A") + right.index(want)) if want in right else "?"
            if given.get(i, given.get(str(i), "")) != want_letter:
                wrong.append(f"{a}→{want_letter}")
        ok = not wrong
        score = (len(left) - len(wrong)) / max(1, len(left))
        return {"pass": ok, "score": score,
                "feedback": "All pairs matched." if ok else
                f"Wrong: {', '.join(wrong)}. Check the study guide."}
    # Batch 6 plugin types: each module owns its grader (pure checklist,
    # AST, or sandbox-verified); every branch handles runner=None itself.
    if t == 15:
        return smellmod.grade(exercise, submission, runner)
    if t == 17:
        return renameexmod.grade(exercise, submission, runner)
    if t == 26:
        return golfmod.grade(exercise, submission, runner)
    if t == 27:
        return diretromod.grade(exercise, submission, runner)
    if t == 28:
        return errbranchmod.grade(exercise, submission, runner)
    if t == 29:
        return logretromod.grade(exercise, submission, runner)
    if t == 31:
        return typeannomod.grade(exercise, submission, runner)
    if t == 32:
        return docdoctestmod.grade(exercise, submission, runner)
    # Execution-graded types need the sandbox runner. Pure-order Parsons
    # (no harness) is graded without it, below.
    if runner is None and not (t == 11 and not p.get("tests")):
        return {"pass": False, "score": 0.0,
                "feedback": "No sandbox available for grading."}
    if t == 8:
        expected = p.get("expected", "").strip()
        res = runner.run(p.get("code", ""))
        ref_ok = res.ok and res.stdout.strip() == expected
        ok = ref_ok and str(submission).strip() == expected
        return {"pass": ok, "score": 1.0 if ok else 0.0,
                "feedback": "Prediction matches." if ok else (
                    "Reference no longer reproduces; flagged stale."
                    if not ref_ok else
                    f"Actual output: {res.stdout.strip()[:200]!r}.")}
    if t == 9:
        expected = [str(x) for x in p.get("expected", [])]
        if not expected:
            return {"pass": False, "score": 0.0,
                    "feedback": "No reference trace available."}
        given = [l.strip() for l in str(submission).splitlines() if l.strip()]
        # Also accept comma/space-separated single-line answers.
        if len(given) == 1 and len(expected) > 1:
            given = [x.strip() for x in given[0].replace(",", " ").split()]
        ok = given == expected
        return {"pass": ok, "score": 1.0 if ok else 0.0,
                "feedback": "Trace matches." if ok else f"Expected {len(expected)} steps; got {given[:8]}"}
    if t == 11:
        if not p.get("tests"):
            # No harness: the shown slice need not run standalone, so the
            # reference order itself is ground truth (same bar as verify).
            return _grade_order(p, submission)
        try:
            idx = [int(x) for x in submission.replace(",", " ").split()]
            ordered = [p["lines"][i] for i in idx]
        except (ValueError, IndexError):
            return {"pass": False, "score": 0.0,
                    "feedback": "Submit space-separated line indices."}
        code = "\n".join(ordered)
        solution = p.get("solution", [])
        res = runner.run(code + "\n" + p.get("tests", ""))
        ok = res.ok and "FAIL" not in res.stdout
        if ok:
            return {"pass": True, "score": 1.0, "feedback": "All green."}
        # Positional feedback: which slots are wrong (1-based).
        bad = [str(i + 1) for i, (a, b) in enumerate(zip(ordered, solution))
               if a != b]
        if len(ordered) != len(solution):
            bad.append(f"length {len(ordered)}≠{len(solution)}")
        right = max(0, len(solution) - len([b for b in bad if b.isdigit()]))
        detail = f"Positions {', '.join(bad)} wrong ({right}/{len(solution)} right). "
        return {"pass": False, "score": 0.0,
                "feedback": detail + f"Output: {res.stdout[:200]} {res.stderr[:200]}"}
    if t in (12, 19, 23):
        # Hidden-tests harness shared by complete, refactor and rebuild:
        # the reference passes, so only the submission is on trial.
        res = runner.run(submission + "\n" + p.get("tests", ""))
        ok = res.ok and "FAIL" not in res.stdout
        return {"pass": ok, "score": 1.0 if ok else 0.0,
                "feedback": "Tests pass." if ok else f"Output: {res.stdout[:300]} {res.stderr[:300]}"}
    if t == 20:
        param = p.get("param", "strict")
        try:
            tree = ast.parse(submission)
        except SyntaxError:
            return {"pass": False, "score": 0.0,
                    "feedback": "Extension does not parse."}
        fns = [n for n in ast.walk(tree)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if not any(_has_default_param(fn, param) for fn in fns):
            return {"pass": False, "score": 0.0,
                    "feedback": f"No optional parameter `{param}=...` found."}
        res = runner.run(submission + "\n" + p.get("tests", ""))
        ok = res.ok and "FAIL" not in res.stdout
        return {"pass": ok, "score": 1.0 if ok else 0.0,
                "feedback": "Extended and green." if ok else
                f"Old behavior broke: {res.stdout[:300]} {res.stderr[:300]}"}
    if t == 14:
        res = runner.run(submission + "\n" + p.get("tests", ""))
        ok = res.ok and "FAIL" not in res.stdout
        return {"pass": ok, "score": 1.0 if ok else 0.0,
                "feedback": "Bug fixed." if ok else f"Still failing: {res.stdout[:300]} {res.stderr[:300]}"}
    return {"pass": False, "score": 0.0, "feedback": "Unknown type."}


# ---------------------------------------------------------------- rendering

def render(exercise: dict) -> str:
    t = exercise["type"]
    # Batch 6 plugin types render through their own module (single source).
    if t == 15:
        return smellmod.render(exercise)
    if t == 17:
        return renameexmod.render(exercise)
    if t == 26:
        return golfmod.render(exercise)
    if t == 27:
        return diretromod.render(exercise)
    if t == 28:
        return errbranchmod.render(exercise)
    if t == 29:
        return logretromod.render(exercise)
    if t == 31:
        return typeannomod.render(exercise)
    if t == 32:
        return docdoctestmod.render(exercise)
    p = exercise.get("payload", {})
    front = html.escape(exercise.get("front", ""))
    body = f"<p>{front}</p>"
    if t == 4:
        opts = "".join(f'<label><input type="radio" name="answer" value="{html.escape(c)}"> {html.escape(c)}</label><br>'
                       for c in p.get("choices", []))
        body += f"<form method='post'>{opts}<button>Submit</button></form>"
    elif t == 11:
        lines = "".join(f"<li>{html.escape(l)} <input name='order' size='2'></li>"
                        for l in p.get("lines", []))
        body += f"<p>Enter the correct order (space-separated indices):</p><form method='post'><input name='answer'><button>Submit</button></form><ol>{lines}</ol>"
    elif t in (12, 14):
        body += f"<form method='post'><textarea name='answer' rows='12' cols='70'>{html.escape(p.get('stub', p.get('buggy', '')))}</textarea><br><button>Run tests</button></form>"
    elif t == 1:
        body += "<form method='post'><input name='answer' placeholder='Recall rating 0-5'><button>Submit</button></form>"
    else:
        body += "<form method='post'><input name='answer' size='60'><button>Submit</button></form>"
    hints = "".join(f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
                    for i, h in enumerate(exercise.get("hints", [])))
    return (f"<article><h3>{html.escape(exercise.get('concept', ''))} "
            f"· {html.escape(exercise.get('type_name', ''))}</h3>"
            f"{body}{hints}"
            f"<p><small>{html.escape(exercise.get('file', ''))}:{exercise.get('line', 0)}</small></p></article>")
