"""Far-transfer challenge (type 75, F-71, bloom: create).

The learner re-expresses a small source pattern in the other language:
Python -> JS/TS or TS/JS -> Python. Three fixed pattern pairs in a catalog
(comprehension -> map/filter, dict.get default -> ?? , str.join -> join);
ex_id hash picks the pair and the direction, so fixtures are deterministic
and fully synthetic. Grading is static: every normalized check token must
appear in the submission (no partial credit — a ported pattern that drops
one behavior drops the pattern). generate never returns None, never raises.
Plugin API: generate(ex_id, concept, snippet, ctx), render(exercise) -> html,
grade(exercise, submission, runner). Import-safe standalone: stdlib only.
"""
from __future__ import annotations
import hashlib
import html

TYPE_NUM = 75
TYPE_NAME = "far-transfer"
BLOOM = "create"
STATUS_ANCHOR = "status-b18-fartransfer"

PATTERNS = (
    {"id": "map-default",
     "py": "nums = [int(x) for x in raw if x.strip()]",
     "ts": "const nums = raw.filter(x => x.trim()).map(x => parseInt(x));",
     "py_checks": ("for", "if", "int("),
     "ts_checks": ("filter", "map", "parseint")},
    {"id": "get-default",
     "py": "val = opts.get('retries', 3)",
     "ts": "const val = opts.retries ?? 3;",
     "py_checks": (".get(", "3"),
     "ts_checks": ("??", "3")},
    {"id": "join",
     "py": "msg = ', '.join(parts)",
     "ts": "const msg = parts.join(', ');",
     "py_checks": (".join(",),
     "ts_checks": (".join(",)},
)

def _concept_field(concept, name, default=""):
    return str(getattr(concept, name, default) or default)

def _pick(ex_id):
    try:
        d = hashlib.sha256(str(ex_id).encode()).hexdigest()
        pat = PATTERNS[int(d[:2], 16) % len(PATTERNS)]
        flip = int(d[2:4], 16) % 2 == 0
    except Exception:
        pat, flip = PATTERNS[0], False
    return pat, flip

def _front_text(src_lang, tgt_lang, source, concept):
    return (
        f"Far transfer: this `{src_lang}` pattern comes from `{concept}`. "
        f"Re-express it in `{tgt_lang}` preserving every behavior "
        f"(filtering, defaults, types):\n```\n{source}\n```")

def _hints():
    return [
        "Map each behavior first: what is filtered, what defaults, what converts?",
        "Target idioms beat transliteration: ?? over ternaries, map/filter over loops.",
        "Worked step: keep the default value identical or the port is wrong.",
    ]

def gen_fartransfer(ex_id, concept, snippet, ctx):
    """Build a far-transfer card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        file = _concept_field(concept, "file", "") or "patterns.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        pat, flip = _pick(ex_id)
        src_lang, tgt_lang = ("python", "typescript") if flip else ("typescript", "python")
        source = pat["py"] if flip else pat["ts"]
        reference = pat["ts"] if flip else pat["py"]
        checks = pat["ts_checks"] if flip else pat["py_checks"]
        grounded = bool(name or any(str(l).strip() for l in snippet))
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", "far-transfer"),
            "concept": name or "far-transfer", "file": file, "line": line,
            "commit": commit, "hints": _hints(),
            "front": _front_text(src_lang, tgt_lang, source, name or "far-transfer"),
            "back": reference,
            "payload": {"pattern": pat["id"], "direction": f"{src_lang}->{tgt_lang}",
                        "source": source, "reference": reference,
                        "check": list(checks), "grounded": grounded},
        }
    except Exception:
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "far-transfer",
            "concept": "far-transfer", "file": "patterns.py", "line": 0,
            "commit": "", "hints": _hints(),
            "front": _front_text("python", "typescript", PATTERNS[0]["py"], "far-transfer"),
            "back": PATTERNS[0]["ts"],
            "payload": {"pattern": "map-default", "direction": "python->typescript",
                        "source": PATTERNS[0]["py"], "reference": PATTERNS[0]["ts"],
                        "check": list(PATTERNS[0]["ts_checks"]), "grounded": False},
        }

def _norm(text):
    return " ".join(str(text).lower().split())

def _fail(msg):
    return {"pass": False, "score": 0.0, "feedback": msg}

def grade(exercise, submission, runner=None):
    """All-check static gate; no partial credit. Never raises."""
    _ = runner
    try:
        p = (exercise or {}).get("payload", {}) or {}
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("Port the pattern — every listed behavior must survive.")
        checks = [c for c in p.get("check", []) if c]
        if not checks or not p.get("reference"):
            return _fail("No transfer checks recorded on this card.")
        normed = _norm(text)
        missed = [c for c in checks if c.lower() not in normed]
        hits = len(checks) - len(missed)
        score = hits / len(checks)
        if not missed:
            return {"pass": True, "score": 1.0,
                    "feedback": f"All {len(checks)} behaviors ported."}
        return {"pass": False, "score": score,
                "feedback": f"Transfer {hits}/{len(checks)} — missing: {', '.join(missed)}."}
    except Exception:
        return _fail("Grader could not read the submission — resubmit.")

def render(exercise):
    """Exercise widget: source pattern plus code textarea."""
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
        f"<p><small>Re-express the pattern in the target language — "
        f"every listed check must hold; no partial credit.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='8' cols='70' "
        f"placeholder='Write the ported pattern here'>"
        f"</textarea><br><button>Check port</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")

def section_html():
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Far-transfer challenge <small>(feature)</small></h3>"
        "<p>Re-express a Python pattern in JS/TS or vice versa — every "
        "behavior must survive the port (static check gate, no partial "
        "credit). <code>groundwork/fartransfer.py</code>.</p>"
    )

def tour_entry():
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "far-transfer", "kind": "feature",
            "title": "Far-transfer challenge",
            "blurb": "Port a pattern to the other language — Python to JS/TS or back — with every behavior intact.",
            "path": "/status", "anchor": "status-b18-fartransfer"}
