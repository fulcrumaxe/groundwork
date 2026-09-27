"""Live param checklist beside the extend-feature editor (I-170).

Type-20 cards grade pass/fail at submit (exercises.grade t==20: the
named param must exist with a default, and hidden tests must stay
green). This module renders those requirements as an unchecked
exists / default / used list beside the code editor; a small client
script ticks items as the learner types (regex approximation).
Advisory only -- grading untouched. Pure functions, stdlib only.
"""
from __future__ import annotations

import ast
import html
import json

STATUS_ANCHOR = "status-b26-extlive"
ETYPE = "20"
DEFAULT_PARAM = "strict"  # mirrors exercises.grade t==20 default


def _field(card, name, default=""):
    """card[name] for dicts and sqlite Rows; default when missing."""
    try:
        return card[name]
    except (KeyError, IndexError, TypeError):
        try:
            return card.get(name, default)
        except AttributeError:
            return default


def param_for(card) -> str:
    """Required param name; grade's own default when absent/hostile."""
    try:
        p = _field(card, "payload", {})
        if isinstance(p, str):
            try:
                p = json.loads(p or "{}")
            except ValueError:
                return DEFAULT_PARAM
        if not isinstance(p, dict):
            return DEFAULT_PARAM
        name = p.get("param", DEFAULT_PARAM)
        if isinstance(name, str) and name:
            return name
        return DEFAULT_PARAM
    except Exception:  # noqa: BLE001 -- checklist never breaks cards
        return DEFAULT_PARAM


def _tree(code):
    """Parsed module or None; never raises."""
    try:
        if not isinstance(code, str) or not code.strip():
            return None
        return ast.parse(code)
    except (SyntaxError, ValueError):
        return None


def _funcs(tree, param) -> list:
    """Functions defining an argument literally named param."""
    out = []
    try:
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            names = [a.arg for a in list(node.args.posonlyargs)
                     + list(node.args.args) + list(node.args.kwonlyargs)]
            if node.args.vararg is not None:
                names.append(node.args.vararg.arg)
            if node.args.kwarg is not None:
                names.append(node.args.kwarg.arg)
            if param in names:
                out.append(node)
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return []
    return out


def exists_in(code, param) -> bool:
    """True when some function defines the parameter (any position)."""
    try:
        tree = _tree(code)
        if tree is None or not param:
            return False
        return bool(_funcs(tree, param))
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return False


def has_default(code, param) -> bool:
    """True when the param carries a default (same bar as the grader)."""
    try:
        tree = _tree(code)
        if tree is None or not param:
            return False
        for fn in _funcs(tree, param):
            positional = list(fn.args.args)
            defaults = list(fn.args.defaults or [])
            if defaults:
                for arg, dflt in zip(positional[len(positional)
                                                - len(defaults):], defaults):
                    if arg.arg == param and dflt is not None:
                        return True
            for arg, dflt in zip(fn.args.kwonlyargs,
                                 fn.args.kw_defaults or []):
                if arg.arg == param and dflt is not None:
                    return True
        return False
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return False


def is_used(code, param) -> bool:
    """True when the param name is read inside a defining function."""
    try:
        tree = _tree(code)
        if tree is None or not param:
            return False
        for fn in _funcs(tree, param):
            for node in ast.walk(fn):
                if (isinstance(node, ast.Name) and node.id == param
                        and isinstance(node.ctx, ast.Load)):
                    return True
        return False
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return False


def status(code, param) -> dict:
    """Server mirror of client ticking: exists/default/used flags."""
    try:
        return {"exists": exists_in(code, param),
                "hasdefault": has_default(code, param),
                "used": is_used(code, param)}
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return {"exists": False, "hasdefault": False, "used": False}


def checklist_html(card_id, param) -> str:
    """Unchecked exists/default/used list; "" when no param (fallback)."""
    try:
        name = param if isinstance(param, str) else ""
        if not name:
            return ""
        esc = html.escape(name, quote=True)
        rows = "".join(
            f"<li data-check='{k}'><span aria-hidden='true'>[ ]</span> "
            f"{label}</li>"
            for k, label in (
                ("exists", f"parameter <code>{esc}</code> exists"),
                ("hasdefault", f"<code>{esc}=...</code> has a default"),
                ("used", f"<code>{esc}</code> is used in the body")))
        return (
            f"<aside class='extlive' "
            f"id='xl-{html.escape(str(card_id))}' data-param='{esc}'>"
            f"<small>Param checklist (advisory - grading unchanged)</small>"
            f"<ul>{rows}</ul></aside>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def script_js() -> str:
    """One guarded listener: tick items on editor input."""
    return """
<script>
if (!window.__extliveInit) { window.__extliveInit = true;
function extliveTick(box) {
  var wrap = box.closest ? box.closest('.extlive-wrap') : null;
  var side = wrap ? wrap.querySelector('.extlive') : null;
  if (!side) return;
  var param = side.getAttribute('data-param') || '';
  if (!param) return;
  var esc = param.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
  var text = box.value || '';
  var seen = (text.match(new RegExp('\\\\b' + esc + '\\\\b', 'g')) || []).length;
  var checks = {exists: seen >= 1,
    hasdefault: new RegExp(esc + '\\\\s*=').test(text),
    used: seen >= 2};
  Array.prototype.forEach.call(side.querySelectorAll('li[data-check]'), function (li) {
    var on = !!checks[li.getAttribute('data-check')];
    li.querySelector('span').textContent = on ? '[x]' : '[ ]';
  });
}
document.addEventListener('input', function (e) {
  var box = e.target.closest ? e.target.closest('.codeedit-input, textarea[name=answer]') : null;
  if (!box) return;
  extliveTick(box);
});
}
</script>"""


def enhance(card, body_html: str) -> str:
    """Editor body + live checklist; legacy bytes when not type 20."""
    try:
        etype = str(_field(card, "exercise_type", ""))
    except (AttributeError, TypeError):
        return body_html
    if etype != ETYPE:
        return body_html
    cid = _field(card, "id", "")
    side = checklist_html(cid, param_for(card))
    if not side:
        return body_html
    return (f"<div class='extlive-wrap'>{body_html}{side}</div>"
            + script_js())


def tour_entry() -> dict:
    """Tour registry entry for the live param checklist."""
    return {"id": "live-param-checklist", "kind": "improvement",
            "title": "Live param checklist",
            "blurb": ("Extend-feature drafts tick exists, default, and "
                      "used live as you type - advisory, never graded."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection with a live-computed sample."""
    try:
        demo = status("def f(x, strict=False):\n"
                      "    return x if not strict else 1\n", "strict")
        marks = " ".join(f"{k}={'[x]' if v else '[ ]'}"
                         for k, v in demo.items())
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Live param checklist "
            "<small>(improvement)</small></h3>"
            "<p>Extend-feature cards show exists / default / used for the "
            "required parameter beside the editor, ticking as you type - "
            "advisory only, grading untouched. "
            "<code>groundwork/extlive.py</code>.</p>"
            f"<p><small>Sample: {html.escape(marks)}</small></p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Live param checklist</h3>"
                "<p>Help unavailable.</p>")
