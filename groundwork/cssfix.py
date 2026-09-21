"""CSS layout fix: repair a broken declaration block to match a wireframe (F-33).

New exercise plugin (type 56, name "css-fix", bloom modify).
The learner gets a wireframe spec (required properties + expected values)
and a broken declaration block, and submits a fixed block. Grading is a
static declaration-set comparison — there is NO browser/pixel-diff in this
environment. Tolerant gate, one line: a spec property passes when present
with a value match after whitespace/case fold; extra harmless properties
are allowed up to MAX_EXTRA; any missing/wrong spec property fails.

The lesson view names the required PROPERTIES but never their expected
values (those are the answer); values live only in the card payload.

Pure functions, stdlib only (hashlib/html/re); no DB, no I/O.
Plugin API: generate(ex_id, concept, snippet, ctx),
render(exercise) -> html, grade(exercise, submission, runner).
Import-safe standalone: imports nothing from groundwork, so
exercises.py can import this module without a cycle.
"""
from __future__ import annotations

import hashlib
import html
import re

TYPE_NUM = 56
TYPE_NAME = "css-fix"
BLOOM = "modify"
STATUS_ANCHOR = "status-b9-cssfix"
MAX_EXTRA = 2  # tolerated harmless extra declarations per submission
DISCLOSURE = (
    "Every spec property must be present with a matching value "
    "(whitespace/case-folded); harmless extras allowed up to 2."
)

_SPECS = [
    {"key": "centered-card", "selector": ".card",
     "goal": "Wireframe: a card whose content is centered both ways.",
     "spec": {"display": "flex", "justify-content": "center",
              "align-items": "center"},
     "broken": (".card {\n  display: block;\n"
                "  justify-content: center;\n}")},
    {"key": "sidebar-row", "selector": ".layout",
     "goal": "Wireframe: sidebar + main side by side with a 16px gap.",
     "spec": {"display": "flex", "flex-direction": "row", "gap": "16px"},
     "broken": (".layout {\n  display: flex;\n"
                "  flex-direction: column;\n}")},
    {"key": "sticky-navbar", "selector": ".nav",
     "goal": "Wireframe: navbar pinned to the viewport top, above content.",
     "spec": {"position": "sticky", "top": "0", "z-index": "10"},
     "broken": (".nav {\n  position: static;\n  top: 0;\n}")},
    {"key": "two-col-grid", "selector": ".grid",
     "goal": "Wireframe: two equal columns with a 12px gap.",
     "spec": {"display": "grid",
              "grid-template-columns": "1fr 1fr", "gap": "12px"},
     "broken": (".grid {\n  display: grid;\n"
                "  grid-template-columns: 1fr;\n}")},
]


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _pick(ex_id: str) -> dict:
    digest = hashlib.sha256(str(ex_id).encode()).hexdigest()
    return _SPECS[int(digest, 16) % len(_SPECS)]


def _fold(value: str) -> str:
    """Whitespace/case fold for tolerant value comparison."""
    return " ".join(str(value).strip().lower().split())


def parse_declarations(text: str) -> dict:
    """Parse a CSS declaration block into {property: folded value}.

    Tolerant: strips /* */ comments, accepts a bare declaration list
    or one wrapped in `selector { ... }`, last duplicate wins.
    Never raises — garbage yields {} (grade then fails closed).
    """
    try:
        body = re.sub(r"/\*.*?\*/", "", str(text), flags=re.S)
        if "{" in body and "}" in body:
            body = body.split("{", 1)[1].rsplit("}", 1)[0]
        out: dict[str, str] = {}
        for chunk in body.split(";"):
            if ":" not in chunk:
                continue
            prop, val = chunk.split(":", 1)
            prop = prop.strip().lower()
            if not prop:
                continue
            out[prop] = _fold(val)
        return out
    except Exception:  # noqa: BLE001 — parser never raises
        return {}


def _fixed_block(spec: dict, selector: str) -> str:
    lines = "\n".join(f"  {p}: {v};" for p, v in spec.items())
    return f"{selector} {{\n{lines}\n}}"


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Deal one css-fix card; never raises on the generic suite ctx."""
    try:
        ctx = ctx or {}
        name = _concept_field(concept, "name", "layout") or "layout"
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        wire = _pick(ex_id)
        spec = dict(wire["spec"])
        required = list(spec)
        fixed = _fixed_block(spec, wire["selector"])
        front = (
            f"CSS layout fix for `{name}`: {wire['goal']}\n"
            f"Repair this declaration block so it carries every required "
            f"property ({', '.join(required)}). Submit the fixed block.\n"
            f"```css\n{wire['broken']}\n```")
        hints = [
            f"Compare each required property ({', '.join(required)}) "
            f"against the broken block — one value is wrong, one property "
            f"is missing.",
            "Values compare after whitespace/case folding, so `1FR  1fr` "
            "still matches `1fr 1fr` — focus on the right properties.",
            f"Worked step: set `{required[0]}: {spec[required[0]]}` first, "
            f"then add the missing property. Up to {MAX_EXTRA} harmless "
            f"extras are allowed.",
        ]
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": hints, "front": front, "back": fixed,
            "payload": {"selector": wire["selector"], "layout": wire["key"],
                        "goal": wire["goal"], "spec": spec,
                        "required": required, "max_extra": MAX_EXTRA,
                        "broken": wire["broken"], "fixed": fixed,
                        "grounded": True},
        }
    except Exception:  # never raise on the generic suite ctx
        spec = {"display": "flex", "justify-content": "center",
                "align-items": "center"}
        fixed = _fixed_block(spec, ".card")
        return {"id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
                "bloom": BLOOM, "concept_id": "layout", "concept": "layout",
                "file": "", "line": 0, "commit": "",
                "hints": ["Match every required property.",
                          "Values ignore whitespace/case.", "Add the missing one."],
                "front": "Fix the `.card` block: display, justify-content, "
                         "align-items.",
                "back": fixed,
                "payload": {"selector": ".card", "layout": "centered-card",
                            "goal": "centered card", "spec": spec,
                            "required": list(spec), "max_extra": MAX_EXTRA,
                            "broken": ".card {\n  display: block;\n}",
                            "fixed": fixed, "grounded": True}}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Pass = every spec property present + value-matching (folded).

    Reports the first mismatch helpfully. Never raises.
    """
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {})
        spec = dict(payload.get("spec", {}) or {})
        required = list(payload.get("required", []) or list(spec))
        max_extra = payload.get("max_extra", MAX_EXTRA)
        try:
            max_extra = int(max_extra)
        except (TypeError, ValueError):
            max_extra = MAX_EXTRA
        if not spec or not required:
            return _fail("Exercise payload is missing the wireframe spec.")
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("Submit the fixed CSS declaration block.")
        got = parse_declarations(text)
        if not got:
            return _fail("No declarations found — submit `prop: value;` lines "
                         "(a bare list or a `selector { ... }` block).")
        matched = 0
        for prop in required:
            want = _fold(spec.get(prop, ""))
            if prop not in got:
                return {"pass": False, "score": matched / len(required),
                        "feedback": f"Missing `{prop}` (expected `{want}`). "
                                    f"({matched}/{len(required)} spec properties "
                                    f"match.) Add it and retry."}
            if got[prop] != want:
                return {"pass": False, "score": matched / len(required),
                        "feedback": f"Wrong `{prop}`: expected `{want}`, got "
                                    f"`{got[prop]}`. ({matched}/{len(required)} "
                                    f"spec properties match.) Fix it and retry."}
            matched += 1
        extras = sorted(set(got) - set(spec))
        if len(extras) > max_extra:
            return {"pass": False, "score": matched / len(required),
                    "feedback": f"Too many extra properties "
                                f"({len(extras)} > {max_extra} allowed: "
                                f"{', '.join(extras)}). Remove the ones the "
                                f"wireframe does not need."}
        return {"pass": True, "score": 1.0,
                "feedback": f"Wireframe matched ({matched}/{len(required)} "
                            f"spec properties"
                            + (f", {len(extras)} harmless extra(s) tolerated."
                               if extras else ".") + ")"}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit CSS.")


def render(exercise: dict) -> str:
    """Css-fix card: goal, required-property names, broken block, textarea.

    Names the required properties but NEVER their expected values —
    the values are the answer and live only in the card payload.
    """
    payload = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    from . import codelines as codelinesmod
    broken = codelinesmod.numbered_html(str(payload.get("broken", "")))
    required = "".join(
        f"<li><code>{html.escape(p)}</code></li>"
        for p in payload.get("required", []))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<p>Required by the wireframe:</p><ul>{required}</ul>"
        f"<pre>{broken}</pre>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>{html.escape(DISCLOSURE)} No browser involved — "
        f"a static declaration-set comparison.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='10' "
        f"cols='60' placeholder='.selector {{\n  prop: value;\n}}'>"
        f"</textarea><br><button>Check CSS</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>CSS layout fix <small>(feature)</small></h3>"
        "<p>Fix a broken CSS declaration block so it matches the wireframe — "
        "graded statically (declaration-set comparison with whitespace/case "
        "tolerance, harmless extras capped), no browser. "
        "<code>groundwork/cssfix.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "css-layout-fix", "kind": "feature",
            "title": "CSS layout fix",
            "blurb": "Fix a broken CSS block to match the wireframe — static tolerant grading.",
            "path": "/status", "anchor": "status-b9-cssfix"}
