"""Flame-graph reading exercise (type 60, F-37, bloom: analyse).

The learner reads a small ASCII flame graph (stack frames with widths
summing to 100%, deterministic from ``ex_id``) where exactly ONE frame
dominates, and must name the dominant frame AND one why-word from a
fixed set. The why-set targets the classic misreading: the hottest
frame is the WIDEST bar (most samples), not the tallest stack or the
leftmost frame — so the correct why-word is always ``widest`` and the
distractors (``tallest``, ``leftmost``) name real visual traps.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only (``hashlib``/``html``/``re``), no
groundwork imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); pipeline needs no skip guard (the
graph is fully synthetic, so there is always a surface).

``generate`` never raises and never returns None for a usable concept:
the graph is synthesized, never planted, so any snippet (even empty)
works. It returns ``None`` only when the concept has no usable name
AND an internal error occurs (defensive; the fixture ctx always yields
a real card with truthy front).
"""
from __future__ import annotations

import hashlib
import html
import re

TYPE_NUM = 60
TYPE_NAME = "flamegraph-reading"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b10-flame"

WHY_WORDS = ("widest", "tallest", "leftmost")
CORRECT_WHY = "widest"

_POOL = ("render", "parse", "query", "encode", "fetch",
         "sort", "hash", "write", "serve", "load")

_NAME_RE = re.compile(r"[^A-Za-z0-9_]")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _clean_name(raw: str) -> str:
    cleaned = _NAME_RE.sub("", str(raw or "").strip())
    if not cleaned or cleaned[0].isdigit():
        return "serve"
    return cleaned[:24]


def _frames(ex_id: str, concept_name: str) -> tuple[list[tuple[str, int]], str]:
    """Five unique frames with widths summing to 100, one dominant.

    Deterministic from ``ex_id``: the head frame (from the concept
    name) takes a dominant share of 45-65%; the other four split the
    remainder with a 5% floor each, then any share above
    ``dom - 15`` is trimmed down so the dominance gap is always >= 15
    points and the dominant frame is always the head. By construction
    the five shares always sum to exactly 100.
    """
    seed = int(hashlib.sha256(str(ex_id).encode()).hexdigest(), 16)
    head = _clean_name(concept_name)
    others = [f for f in _POOL if f != head]
    rot = seed % len(others)
    names = [head] + (others[rot:] + others[:rot])[:4]
    dom = 45 + (seed >> 8) % 21  # 45..65
    rest = 100 - dom  # 35..55
    span = rest - 20  # free points above the 5% floor (>= 15)
    cuts = sorted((seed >> (16 + 11 * i)) % (span + 1) for i in range(3))
    bounds = [0] + cuts + [span]
    shares = [b - a + 5 for a, b in zip(bounds, bounds[1:])]
    cap = dom - 15
    for _ in range(100):
        big = max(shares)
        if big <= cap:
            break
        i = shares.index(big)
        j = min((k for k in range(4) if k != i),
                key=lambda k: shares[k])
        shares[i] -= 1
        shares[j] += 1
    widths = sorted(shares, reverse=True)
    ordered = [(names[0], dom)] + list(zip(names[1:], widths))
    ordered.sort(key=lambda kv: -kv[1])
    return ordered, names[0]


def _ascii_graph(frames: list[tuple[str, int]]) -> str:
    width = max(len(n) for n, _ in frames)
    lines = []
    for name, pct in frames:
        bar = "#" * max(1, pct * 40 // 100)
        lines.append(f"{name.ljust(width)} |{bar.ljust(40)}| {pct}%")
    return "\n".join(lines)


def _hints(dominant: str, file: str, line: int) -> list[str]:
    where = f"{file}:{line}" if file and line else (file or "the linked file")
    return [
        "Width is heat: the frame with the widest bar owns the most samples.",
        f"Look at {where}: one bar is far wider than the rest — name that frame.",
        f"Worked step: reply `frame={dominant}` on one line and `why=widest` on the next.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a flame-graph card; None only when nothing grounds it."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        name = _concept_field(concept, "name", "")
        if not name:
            return None
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        frames, dominant = _frames(str(ex_id), name)
        graph = _ascii_graph(frames)
        front = (
            "One frame below dominates the profile. Reply with the "
            "dominant frame name AND one why-word "
            f"({', '.join(WHY_WORDS)}).\n"
            f"```\n{graph}\n```\n"
            "Widths = share of total samples."
        )
        back = (f"`{dominant}` dominates ({dict(frames)[dominant]}% of "
                f"samples) because it is the {CORRECT_WHY} bar.")
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": _hints(dominant, file, line),
            "front": front, "back": back,
            "payload": {"frames": [[n, p] for n, p in frames],
                        "dominant": dominant, "why": CORRECT_WHY,
                        "why_words": list(WHY_WORDS), "grounded": True},
        }
    except Exception:
        return None  # generate never raises


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def normalize_frame(text: str) -> str:
    """Lowercase, strip quotes/backticks/whitespace and any trailing call
    suffix (``(...)``) or percentage — nothing else."""
    t = str(text if text is not None else "").strip().lower()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in ("'", '"', "`"):
        t = t[1:-1].strip()
    t = re.split(r"[\s(:%]", t, 1)[0]
    return _NAME_RE.sub("", t)


def _parse_fields(submission: str) -> dict:
    """Accept `frame=`/`why=` lines or a two-line `name`/`word` answer."""
    out: dict = {}
    for line in str(submission).splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            k = k.strip().lower()
            if k in ("frame", "why"):
                out[k] = v.strip()
    if "frame" not in out or "why" not in out:
        bare = [l.strip() for l in str(submission).splitlines() if l.strip()]
        if len(bare) == 2 and "=" not in str(submission):
            out.setdefault("frame", bare[0])
            out.setdefault("why", bare[1])
    return out


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Pass only when BOTH the dominant frame and the why-word match."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        dominant = str(payload.get("dominant", "") or "")
        why = str(payload.get("why", "") or CORRECT_WHY)
        if not dominant:
            return _fail("Exercise payload is missing the dominant frame.")
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("Submit the dominant frame name and one why-word.")
        fields = _parse_fields(text)
        frame_ok = normalize_frame(fields.get("frame", "")) == normalize_frame(dominant)
        why_ok = str(fields.get("why", "")).strip().lower() == why.lower()
        if frame_ok and why_ok:
            return {"pass": True, "score": 1.0,
                    "feedback": f"`{dominant}` is the widest bar — most samples."}
        if not frame_ok and not why_ok:
            return _fail("Neither the frame nor the why-word matches — widest bar wins, "
                         f"one of: {', '.join(WHY_WORDS)}.")
        if not frame_ok:
            return _fail("Not the dominant frame — compare bar widths, not height or position.")
        return _fail(f"Right frame, wrong reason — pick one of: {', '.join(WHY_WORDS)}.")
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit frame + why-word.")


def render(exercise: dict) -> str:
    """Exercise widget: ASCII flame graph plus frame/why answer boxes."""
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
        f"<p><small>Exact dominant frame name plus one why-word "
        f"({', '.join(WHY_WORDS)}) — both required, substrings and "
        f"graph dumps do not count.</small></p></details>"
        f"<form method='post'><input name='frame' size='30' "
        f"placeholder='dominant frame name'>"
        f"<input name='why' size='12' placeholder='widest/tallest/leftmost'>"
        f"<button>Name the hotspot</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Flame-graph reading <small>(feature)</small></h3>"
        "<p>Name the frame that dominates a flame graph and say why — "
        "the widest bar owns the most samples, not the tallest or "
        "leftmost. Graded by exact frame match plus one why-word "
        "(widest/tallest/leftmost); both required, fail closed. "
        "<code>groundwork/flame.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "flamegraph-reading", "kind": "feature",
            "title": "Flame-graph reading",
            "blurb": "Spot the frame that dominates a flame graph — name it and say why (widest bar wins).",
            "path": "/status", "anchor": "status-b10-flame"}
