"""Code-reading fluency drill (type 79, F-75, bloom: understand).

The learner skims a short snippet under a time budget, forms a one-line
gist, then verifies it against three machine-checkable probes: a keyword
probe (which token appears), a locate probe (which line holds the key
name), and an owner probe (which file it comes from). Submission is the
probe letters in order (``BCA``); all correct passes, partial credit per
probe. The budget is self-enforced and shown up front — async review has
no wall clock — so the card drills the skim-then-check loop honestly.

``generate`` never returns None and never raises: thin input yields an
ungrounded card the pipeline skips. Import-safe standalone: stdlib only,
no groundwork imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES), ``groundwork/select.py``
(beginner map), ``groundwork/grading.py`` (disclosure table),
``groundwork/__main__.py`` (cmd_e2e fixture), ``groundwork/bloomchips.py``
(tier color); ``cards.py`` needs no change (generic else covers 79).
Status section and tour entry below (wired via batch18.py).
"""

from __future__ import annotations

import hashlib
import html
import random
import re

TYPE_NUM = 79
TYPE_NAME = "reading-fluency"
BLOOM = "understand"
STATUS_ANCHOR = "status-b18-fluency"

TIME_S = 90
MAX_LINES = 10
_FENCE = "`" * 3  # computed so the source holds no literal fence

_KEYWORDS = ["return", "import", "def ", "if ", "for ", "while ", "="]
_STOP = {"def", "return", "if", "else", "elif", "for", "while", "in",
        "import", "from", "None", "True", "False", "self", "print",
        "assert", "with", "as", "class", "pass", "and", "or", "not",
        "is", "raise", "try", "except", "finally", "lambda", "await"}


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _seed(ex_id) -> int:
    try:
        return int(hashlib.sha256(str(ex_id).encode()).hexdigest()[:8], 16)
    except Exception:  # noqa: BLE001 — seeding must never raise
        return 0


def _code_lines(snippet) -> list[str]:
    try:
        lines = [str(l).rstrip() for l in (snippet or [])]
    except Exception:  # noqa: BLE001 — bad input still drafts
        return []
    return [l for l in lines if l.strip()][:MAX_LINES]


def _top_name(lines: list[str], concept_name: str) -> tuple[str, int]:
    """Most frequent non-stop identifier and its first 1-based line."""
    freq: dict[str, int] = {}
    for w in re.findall(r"[A-Za-z_]\w*", "\n".join(lines)):
        if len(w) >= 2 and w not in _STOP:
            freq[w] = freq.get(w, 0) + 1
    ordered = ([concept_name] if concept_name else []) + sorted(
        freq, key=lambda w: -freq[w])
    for name in ordered:
        for i, l in enumerate(lines):
            if name and name in l:
                return name, i + 1
    return concept_name or "it", 1


def _probes(ex_id, concept_name: str, concept_file: str,
            lines: list[str], graph) -> list[dict]:
    rng = random.Random(_seed(ex_id))
    out: list[dict] = []
    # 1. keyword probe: which of these tokens appears in the snippet?
    present = next((k for k in _KEYWORDS if any(k in l for l in lines)), "")
    if present:
        pool = [k for k in _KEYWORDS
                if not any(k in l for l in lines)][:2]
        choices = [present.strip() or present] + [c.strip() or c for c in pool]
        while len(choices) < 3:
            choices.append("a comment line")
        rng.shuffle(choices)
        out.append({"q": "Which of these tokens appears in the snippet?",
                    "choices": choices[:3],
                    "answer": (present.strip() or present)})
    # 2. locate probe: which line holds the key name?
    name, lineno = _top_name(lines, concept_name)
    others = [n for n in (lineno - 1, lineno + 1, 1, len(lines))
              if 1 <= n <= max(1, len(lines)) and n != lineno][:2]
    while len(others) < 2:
        others.append(max(1, len(lines)))
    choices = [f"line {lineno}"] + [f"line {n}" for n in others[:2]]
    rng.shuffle(choices)
    out.append({"q": f"Which line mentions `{name}`?",
                "choices": choices[:3], "answer": f"line {lineno}"})
    # 3. owner probe: which file does this snippet come from?
    files = []
    try:
        files = sorted({n.file for n in graph.nodes.values()}) \
            if graph is not None else []
    except Exception:  # noqa: BLE001 — graph trouble still drafts
        files = []
    distract = [f for f in files if f != concept_file][:2]
    distract += ["the test suite", "another module"]
    choices = [concept_file] + distract[:2]
    rng.shuffle(choices)
    out.append({"q": "Which file does this snippet come from?",
                "choices": choices[:3], "answer": concept_file})
    return out


def _hints() -> list[str]:
    return [
        f"Skim first ({TIME_S}s budget) — structure, names, shape; do not read every token.",
        "Say the gist in one line aloud, then let the probes check you.",
        "Worked step: key name → its line → its file bounds every probe.",
    ]


def _front(n: int) -> str:
    return (
        f"Skim the snippet below ({TIME_S}s budget), form a one-line gist, "
        f"then verify it: reply with the {n} probe letters in order "
        f"(e.g. `BCA`). All correct passes; partial credit per probe."
    )


def generate(ex_id, concept, snippet, ctx):
    """Build a gist-then-verify card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        lines = _code_lines(snippet)
        name = _concept_field(concept, "name", "")
        file = _concept_field(concept, "file", "") or "unknown.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        probes = _probes(ex_id, name, file, lines, ctx.get("graph"))
        letters = "ABC"
        key = "".join(letters[p["choices"].index(p["answer"])]
                      for p in probes)
        grounded = bool(lines)  # probes need snippet lines; thin input skips
        numbered = "\n".join(f"{i + 1}: {l}" for i, l in enumerate(lines))
        shown = "\n".join(
            f"Probe {i + 1}: {p['q']} "
            f"({', '.join(f'{L}={c}' for L, c in zip(letters, p['choices']))})"
            for i, p in enumerate(probes))
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", "fluency"),
            "concept": name or "fluency", "file": file, "line": line,
            "commit": commit, "hints": _hints(),
            "front": f"{_front(len(probes))}\n{_FENCE}\n{numbered}\n{_FENCE}\n{shown}",
            "back": f"{key} — " + "; ".join(
                f"Probe {i + 1}: {p['answer']}" for i, p in enumerate(probes)),
            "payload": {"lines": numbered, "probes": probes, "key": key,
                        "time_s": TIME_S, "reference": key,
                        "grounded": grounded},
        }
    except Exception:
        return {  # generate never raises and never returns None
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "fluency", "concept": "fluency",
            "file": "unknown.py", "line": 0, "commit": "",
            "hints": _hints(), "front": _front(0),
            "back": "No snippet recorded on this card.",
            "payload": {"lines": "", "probes": [], "key": "",
                        "time_s": TIME_S, "reference": "",
                        "grounded": False},
        }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _letters(submission: str, n: int) -> list[str] | None:
    """Compact letters (``BCA``/``b c,a``) or keyed lines (``0=B``)."""
    text = str(submission if submission is not None else "")
    keyed: dict[int, str] = {}
    try:
        for line in text.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                keyed[int(k.strip())] = v.strip().upper()[:1]
    except (ValueError, TypeError):
        pass
    if keyed:
        try:
            return [keyed[i] for i in range(n)]
        except KeyError:
            return None
    toks = re.findall(r"[A-Za-z]", text)
    if len(toks) != n:
        return None
    return [t.upper() for t in toks]


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """All-correct passes; partial credit per probe; never raises."""
    _ = runner
    try:
        p = (exercise or {}).get("payload", {}) or {}
        probes = p.get("probes", []) or []
        key = str(p.get("key", "") or "")
        if not probes or not key:
            return _fail("No verify probes recorded on this card.")
        given = _letters(submission, len(probes))
        if given is None:
            return _fail(f"Reply with the {len(probes)} probe letters "
                         f"in order (e.g. `{key}`).")
        want = list(key.upper())
        right = sum(1 for g, w in zip(given, want) if g == w)
        if right == len(want):
            return {"pass": True, "score": 1.0,
                    "feedback": f"Gist verified — all {len(want)} probes green."}
        bad = [str(i + 1) for i, (g, w) in enumerate(zip(given, want))
               if g != w]
        return {"pass": False, "score": right / max(1, len(want)),
                "feedback": f"Probe(s) {', '.join(bad)} wrong "
                            f"({right}/{len(want)} right). Re-skim and retry."}
    except Exception as exc:  # noqa: BLE001 — grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def render(exercise: dict) -> str:
    """Exercise widget: numbered snippet, probes, one answer input."""
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Skim-then-verify: every probe letter must match — "
        f"all correct passes, partial credit per probe.</small></p></details>"
        f"<form method='post'><input name='answer' size='10' "
        f"placeholder='Probe letters, e.g. BCA'>"
        f"<button>Verify gist</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by batch18.py."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Reading fluency <small>(feature)</small></h3>"
        "<p>Skim a snippet on a 90s budget, form a one-line gist, then "
        "verify it against three probes — keyword, locate, owner. "
        "All probe letters correct passes, partial credit per probe. "
        "<code>groundwork/fluency.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by batch18.py)."""
    return {"id": "reading-fluency", "kind": "feature",
            "title": "Reading fluency",
            "blurb": "Skim a snippet on a 90s budget, gist it in one line, then verify with three probes — keyword, locate, owner.",
            "path": "/status", "anchor": "status-b18-fluency"}
