"""Worked-example own-inputs widget (I-106): re-run the worked example
with the learner's own inputs, in-page.

Client-side only (no new route): editable per-argument fields rebuild
the call text in-page, persist per lesson in localStorage, and offer
copyable neighbor-variant calls. Lessons without a parsable worked
call render "" (legacy fallback). Stdlib only (`ast`, `html`); never
raises.
"""
from __future__ import annotations

import ast
import html

STATUS_ANCHOR = "status-b19-runinputs"

MAX_ARGS = 6
MAX_TEXT = 200
MAX_VARIANTS = 4


def parse_call(call) -> dict:
    """{"func", "args"} for a literal-arg call; {} otherwise.

    `ast`-parsed; the callee must be a bare Name and every argument
    must round-trip through `ast.literal_eval`. Never raises.
    """
    try:
        if not isinstance(call, str) or not call.strip():
            return {}
        tree = ast.parse(call.strip(), mode="eval")
        node = tree.body
        if not isinstance(node, ast.Call):
            return {}
        if not isinstance(node.func, ast.Name):
            return {}
        if node.keywords or len(node.args) > MAX_ARGS:
            return {}
        args = []
        for a in node.args:
            if isinstance(a, ast.Starred):
                return {}
            try:
                v = ast.literal_eval(a)
            except (ValueError, SyntaxError, TypeError, MemoryError,
                    RecursionError):
                return {}
            args.append(repr(v)[:MAX_TEXT])
        return {"func": node.func.id, "args": args}
    except (SyntaxError, ValueError, MemoryError, RecursionError):
        return {}
    except Exception:  # noqa: BLE001 -- parsing never raises
        return {}


def suggest_variants(func: str, args: list) -> list:
    """Up to MAX_VARIANTS neighbor calls from literal args; never raises."""
    try:
        if not isinstance(func, str) or not func:
            return []
        if not isinstance(args, list) or not args:
            return []
        vals = []
        for a in args:
            try:
                vals.append(ast.literal_eval(a))
            except (ValueError, SyntaxError, TypeError, MemoryError,
                    RecursionError):
                return []
        out = []
        for i, v in enumerate(vals):
            if isinstance(v, bool):
                continue
            if isinstance(v, int):
                for nv in (v - 1, v + 1):
                    out.append(_call(func, vals, i, nv))
                    if len(out) >= MAX_VARIANTS:
                        return out
                return out
            if isinstance(v, float):
                for nv in (v - 1.0, v + 1.0):
                    out.append(_call(func, vals, i, nv))
                    if len(out) >= MAX_VARIANTS:
                        return out
                return out
            if isinstance(v, str) and v:
                out.append(_call(func, vals, i, v.swapcase()))
                return out
        return out
    except Exception:  # noqa: BLE001
        return []


def _call(func: str, vals: list, i: int, nv) -> str:
    rep = [repr(nv if j == i else v) for j, v in enumerate(vals)]
    return f"{func}({', '.join(rep)})"


def runinputs_html(lesson: dict) -> str:
    """Editable-inputs details widget for the worked call; "" when unusable."""
    try:
        if not isinstance(lesson, dict):
            return ""
        worked = lesson.get("worked") or {}
        if not isinstance(worked, dict):
            return ""
        parsed = parse_call(worked.get("call"))
        if not parsed:
            return ""
        func = parsed["func"]
        call = f"{func}({', '.join(parsed['args'])})"
        output = html.escape(str(worked.get("output") or ""))
        fields = []
        for i, a in enumerate(parsed["args"]):
            fields.append(
                f"<label>arg{i + 1} "
                f"<input class='ri-field' name='ri{i}' size='12' "
                f"value='{html.escape(a, quote=True)}'></label>")
        variants = "".join(
            f"<li><code>{html.escape(v)}</code></li>"
            for v in suggest_variants(func, parsed["args"]))
        variants_html = f"<ul>{variants}</ul>" if variants else ""
        return (
            f"<details id='runinputs' data-rifunc='{html.escape(func, quote=True)}' "
            f"data-rikey='gw-ri:{html.escape(call, quote=True)}'>"
            f"<summary>Try your own inputs</summary>"
            f"<p><small>Measured: <code>{html.escape(call)}</code>"
            f" gives <code>{output}</code>. Change the arguments — your call rebuilds below.</small></p>"
            f"<p>{' '.join(fields)}</p>"
            f"<p><small>Your call: <output class='ri-out'></output></small></p>"
            f"{variants_html}"
            f"<p><small>Try a variant in your own Python REPL, then come back.</small></p>"
            f"<script>(function(){{"
            f"var d=document.currentScript.closest('details');if(!d)return;"
            f"var key=d.getAttribute('data-rikey');var func=d.getAttribute('data-rifunc');"
            f"var out=d.querySelector('.ri-out');"
            f"var fields=d.querySelectorAll('.ri-field');"
            f"function vals(){{return Array.prototype.map.call(fields,function(f){{return f.value;}});}}"
            f"function paint(){{if(out)out.textContent=func+'('+vals().join(', ')+')';}}"
            f"try{{var saved=JSON.parse(localStorage.getItem(key)||'[]');"
            f"Array.prototype.forEach.call(fields,function(f,i){{if(saved[i]!==undefined)f.value=saved[i];}});}}catch(e){{}}"
            f"Array.prototype.forEach.call(fields,function(f){{f.addEventListener('input',function(){{paint();"
            f"try{{localStorage.setItem(key,JSON.stringify(vals()));}}catch(e){{}}}});}});"
            f"paint();}})();</script>"
            f"</details>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch19 home module."""
    sample = runinputs_html({"worked": {"call": "add(2, 3)", "output": "5"}})
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Run-your-own-inputs <small>(improvement)</small></h3>"
        "<p>Every worked example grows editable inputs: change the arguments, "
        "see your call rebuilt in-page, and try neighbor variants. "
        "<code>groundwork/runinputs.py</code> parses the stored call on the "
        "lesson rendering path (<code>lessons.render_levels</code>); lessons "
        "without a usable call render exactly as before. A live sample renders "
        "below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "run-own-inputs",
        "kind": "improvement",
        "title": "Run the worked example yourself",
        "blurb": "Every worked example grows editable inputs: change the "
                 "arguments, see your call rebuilt in-page, and try neighbor "
                 "variants.",
        "path": "/modules/{mid}",
        "anchor": "runinputs",
    }
