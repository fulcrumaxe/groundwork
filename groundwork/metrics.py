"""Metrics-reading exercise (type 59, F-36, bloom: analyse).

The learner reads three small text metric series (e.g. latency p99,
error rate, throughput, CPU) with a marked deploy point and must name
which graph shows the regression. Exactly one graph regresses at the
deploy mark (deterministic from ``ex_id``); the other two stay flat or
improve. Grading is an exact single-letter match (A/B/C) after
documented normalization: surrounding whitespace/case and an optional
``graph``/``option`` prefix are ignored, nothing else — a pasted dump
of the series (which contains every letter and digit) must NOT pass.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only (``hashlib``/``html``/``random``/
``re``), no groundwork imports. Registration lives in
``groundwork/exercises.py`` (TYPES, GENERATORS, BLOOM_TYPES).

``generate`` never raises and never returns None: the series are fully
synthetic, so unlike snippet-grounded types there is always a
plantable surface (this is what ``test_all_types_generate`` needs).
"""
from __future__ import annotations

import hashlib
import html
import random
import re

TYPE_NUM = 59
TYPE_NAME = "metrics-reading"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b10-metrics"

N_PRE, N_POST = 6, 6
LETTERS = ("A", "B", "C")

# (label, unit, base value, worsening direction, decimals)
_METRICS = (
    ("latency p99", "ms", 120.0, "up", 0),
    ("error rate", "%", 1.0, "up", 1),
    ("throughput", "req/s", 800.0, "down", 0),
    ("cpu", "%", 45.0, "up", 0),
)

_LETTER_RE = re.compile(
    r"^(?:graph|option)?\s*#?\s*([abc])\s*\.?\s*$", re.IGNORECASE)


def _concept_field(concept, name: str, default: str = "") -> str:
    try:
        return str(getattr(concept, name, default) or default)
    except Exception:
        return default


def _seed(ex_id) -> random.Random:
    digest = hashlib.sha256(f"metrics:{ex_id}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _fmt(value: float, decimals: int) -> str:
    return f"{value:.{decimals}f}" if decimals else str(int(round(value)))


def _series(rng: random.Random, base: float, kind: str,
            worse: str) -> list[float]:
    """Flat-with-noise prelude; postlude depends on kind.

    ``kind`` is one of "regress" (steps worse after deploy), "flat"
    (noise only), or "better" (steps the good direction after deploy).
    """
    pre = [base * rng.uniform(0.95, 1.05) for _ in range(N_PRE)]
    if kind == "regress":
        factor = 1.5 if worse == "up" else 0.6
        post = [base * factor * rng.uniform(0.95, 1.05)
                for _ in range(N_POST)]
    elif kind == "better":
        factor = 0.8 if worse == "up" else 1.2
        post = [base * factor * rng.uniform(0.95, 1.05)
                for _ in range(N_POST)]
    else:
        post = [base * rng.uniform(0.95, 1.05) for _ in range(N_POST)]
    return pre + post


def _bars(values: list[float]) -> list[str]:
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    return ["#" * (1 + int(19 * (v - lo) / span)) for v in values]


def _render_graph(letter: str, label: str, unit: str,
                  values: list[float], decimals: int) -> str:
    bars = _bars(values)
    lines = []
    for i, (v, b) in enumerate(zip(values, bars)):
        mark = " | " if i == N_PRE else "   "
        lines.append(f"{mark}t{i:02d} {_fmt(v, decimals):>7} {unit} {b}")
    head = f"{letter}. {label} ({unit}) — deploy at |"
    return head + "\n" + "\n".join(lines)


def _hints(answer: str, label: str, file: str, line: int) -> list[str]:
    where = f"{file}:{line}" if file and line else (file or "the linked file")
    return [
        "Compare pre vs post on each graph: a regression is a step "
        "change at the | mark, not point-to-point noise.",
        f"Look at {where}: exactly one of A/B/C moves the wrong way "
        "after the deploy — reply with its letter alone.",
        f"Worked step: the answer is one letter (e.g. `{answer}` for "
        f"{label}); `graph {answer.lower()}` also counts.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a metrics-reading card; always returns a card, never raises.

    The regressing-graph index, the three metrics, and the noise all
    derive from a ``sha256("metrics:{ex_id}")`` seed, so the same
    ``ex_id`` rebuilds the same card. Snippet/ctx are accepted for the
    Plugin API shape but unused — the card is fully synthetic.
    """
    try:
        rng = _seed(ex_id)
        name = _concept_field(concept, "name", "") or "service"
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str((ctx if isinstance(ctx, dict) else {}).get("commit", "")
                     or "")
        picked = rng.sample(list(_METRICS), 3)
        reg_idx = rng.randrange(3)
        kinds = ["flat", "better"]
        rng.shuffle(kinds)
        graphs, blocks = [], []
        for i, (label, unit, base, worse, dec) in enumerate(picked):
            kind = "regress" if i == reg_idx else kinds.pop()
            values = _series(rng, base, kind, worse)
            pre = sum(values[:N_PRE]) / N_PRE
            post = sum(values[N_PRE:]) / N_POST
            graphs.append({"letter": LETTERS[i], "label": label,
                           "unit": unit, "kind": kind,
                           "pre": round(pre, 2), "post": round(post, 2)})
            blocks.append(_render_graph(LETTERS[i], label, unit,
                                        values, dec))
        answer = LETTERS[reg_idx]
        winner = graphs[reg_idx]
        front = (
            "Three metric series span one deploy (marked |). Exactly ONE "
            "graph shows a regression at the deploy — the others stay "
            "flat or improve. Reply with the single letter A, B, or C.\n"
            f"```\n{chr(10).join(blocks)[:1200]}\n```"
        )
        back = (f"Graph {answer} ({winner['label']}) regressed at the "
                f"deploy: avg {winner['pre']} -> {winner['post']} "
                f"{winner['unit']}.")
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": _hints(answer, winner["label"], file, line),
            "front": front, "back": back,
            "payload": {"graphs": graphs, "choices": list(LETTERS),
                        "answer": answer, "grounded": True},
        }
    except Exception:
        return None  # grading-grade safety: generate never raises


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def normalize_letter(text: str) -> str:
    """Isolated A/B/C (optional graph/option prefix), else "".

    Strict by design: digits buried in a pasted series, multi-letter
    prose, and dumps of all three graphs never count — only an
    isolated letter guess does. Never raises.
    """
    try:
        m = _LETTER_RE.match(str(text if text is not None else ""))
        return m.group(1).upper() if m else ""
    except Exception:
        return ""


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Exact-letter match against the regressing graph."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        answer = str(payload.get("answer", "") or "").upper()
        if answer not in LETTERS:
            return _fail("Exercise payload is missing the regressing graph.")
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("Reply with the single letter of the regressing graph.")
        if normalize_letter(text) == answer:
            return {"pass": True, "score": 1.0,
                    "feedback": f"Graph {answer} shows the regression."}
        return _fail("Not the regressing graph — compare pre vs post at the | mark.")
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — reply with one letter.")


def render(exercise: dict) -> str:
    """Exercise widget: three series plus A/B/C radio options."""
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    payload = exercise.get("payload", {}) or {}
    graphs = payload.get("graphs", []) or []
    if graphs:
        opts = "".join(
            f'<label><input type="radio" name="answer" value="{g["letter"]}"> '
            f'<b>{html.escape(str(g["letter"]))}.</b> '
            f'{html.escape(str(g.get("label", "")))}</label><br>'
            for g in graphs)
    else:
        opts = "".join(
            f'<label><input type="radio" name="answer" value="{L}"> '
            f'<b>{L}</b></label><br>' for L in LETTERS)
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Exact single letter A, B, or C — pasted series "
        f"or prose does not count.</small></p></details>"
        f"<form method='post'>{opts}<button>Pick the regression</button></form>"
        f"{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Metrics reading <small>(feature)</small></h3>"
        "<p>Three metric series span one deploy — name the single graph "
        "that regresses at the deploy mark. Graded by exact single-letter "
        "match; distractors stay flat or improve. "
        "<code>groundwork/metrics.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "metrics-reading", "kind": "feature",
            "title": "Metrics reading",
            "blurb": "Spot which graph regressed at the deploy mark — reply with its letter.",
            "path": "/status", "anchor": "status-b10-metrics"}
