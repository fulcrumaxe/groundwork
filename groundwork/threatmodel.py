"""Threat-model-the-function exercise (type 49, F-26, bloom: analyse).

The learner reads a real function snippet and lists its abuse cases /
threat-model items (injection surfaces, unvalidated inputs, auth gaps,
secret handling). The checklist is derived statically (``ast`` + line
scans) — deterministic, sandbox-free, import-safe standalone: stdlib
only (``ast``/``re``/``html``), no groundwork imports.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); pipeline needs no skip guard.

No attack surface (or analysis failure) yields an ungrounded card
the emission loop drops — never ``None``, so the all-types-generate
contract holds. It never raises.
"""
from __future__ import annotations

import ast
import html
import re

TYPE_NUM = 49
TYPE_NAME = "threat-model"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b9-threatmodel"

CODE_LIMIT = 800
MAX_ITEMS = 6  # checklist stays reviewable; detectors run in fixed order

# Detector = (item_id, label, key phrases for tolerant matching).
# Order is the presentation order (fixed => deterministic).
DETECTORS = (
    ("code-injection", "Code injection: untrusted input reaches eval()/exec()/compile()",
     ("code injection", "eval", "exec")),
    ("command-injection", "Command injection: user text reaches a shell",
     ("command injection", "shell", "subprocess", "os.system", "shell=true")),
    ("sql-injection", "SQL injection: query built with %/format/f-string into execute()",
     ("sql injection", "execute", "query")),
    ("path-traversal", "Path traversal: open() on an unvalidated path",
     ("path traversal", "arbitrary file", "open(")),
    ("ssrf", "Server-side request forgery: unvalidated URL fetched",
     ("request forgery", "ssrf", "unvalidated url", "requests", "urllib")),
    ("deserialization", "Unsafe deserialization: untrusted bytes to pickle/yaml.load",
     ("deserial", "pickle", "yaml.load", "marshal")),
    ("hardcoded-secret", "Hardcoded secret: password/token/key literal in source",
     ("hardcoded secret", "password", "api key", "token", "secret")),
    ("unvalidated-input", "Unvalidated input: parameter reaches a sink unguarded",
     ("unvalidated", "validation", "sanitize", "no check")),
    ("auth-gap", "Missing authorization check on a user/role/token parameter",
     ("authorization", "auth", "permission", "access control")),
    ("broad-except", "Overbroad except hides attack evidence",
     ("broad except", "bare except", "swallow")),
)

_EVALISH = {"eval", "exec", "compile"}
_SHELLISH = {"system", "popen", "call", "run", "Popen"}
_NETISH = {"get", "post", "put", "request", "urlopen", "urlretrieve",
           "Urlopen", "fetch"}
_SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret|password|passwd|auth[_-]?token|access[_-]?token)"
    r"\s*[:=]\s*['\"][^'\"]{2,}['\"]")
_VALIDATE_TOKENS = ("assert", "raise", "ValueError", "TypeError", "if not",
                    "sanitize", "escape", "allowlist", "allow_list",
                    "validate", "check_")
_AUTH_PARAMS = {"user", "username", "uid", "role", "admin", "token",
                "session", "auth", "permission", "password"}
_AUTH_TOKENS = ("auth", "permission", "role", "allow", "deny", "check_",
                "verify", "403", "401", "forbidden", "unauthorized")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _code_of(snippet) -> str:
    if isinstance(snippet, str):
        return snippet
    try:
        return "\n".join(str(l) for l in (snippet or []))
    except TypeError:
        return ""


def _tree(code: str):
    try:
        return ast.parse(code)
    except (SyntaxError, ValueError):
        return None


def _call_names(tree) -> list[tuple[str, str]]:
    """(dotted callee, keyword-args source) for every call in the tree."""
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Name):
            out.append((f.id, ast.dump(node)))
        elif isinstance(f, ast.Attribute):
            base = f.value.id if isinstance(f.value, ast.Name) else "?"
            out.append((f"{base}.{f.attr}",
                        f"{base}.{f.attr} {ast.dump(node)}"))
    return out


def _detect_from_tree(code: str, tree) -> list[str]:
    found: list[str] = []

    def add(item: str) -> None:
        if item not in found:
            found.append(item)

    calls = _call_names(tree)
    names = [c for c, _ in calls]
    if any(n.split(".")[-1] in _EVALISH for n in names):
        add("code-injection")
    if any(n in ("os.system", "os.popen") or n.split(".")[-1] in _SHELLISH
           for n in names) or "shell=True" in code:
        add("command-injection")
    if any(n.split(".")[-1] in ("execute", "executemany") for n in names) \
            and ("%" in code or ".format(" in code or "f\"" in code
                 or "f'" in code):
        add("sql-injection")
    if any(n == "open" or n.split(".")[-1] == "open" for n in names):
        add("path-traversal")
    if any(n.split(".")[-1] in _NETISH or n.startswith(("requests.",
            "urllib.", "httpx.", "http.")) for n in names):
        add("ssrf")
    if any(n in ("pickle.loads", "marshal.loads", "yaml.load",
                 "shelve.open") for n in names):
        add("deserialization")
    if _SECRET_RE.search(code):
        add("hardcoded-secret")
    handlers = [h for h in ast.walk(tree)
                if isinstance(h, ast.ExceptHandler)]
    if any(h.type is None or
           (isinstance(h.type, ast.Name)
            and h.type.id in ("Exception", "BaseException"))
           for h in handlers):
        add("broad-except")
    params: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            params.update(a.arg for a in node.args.args)
            params.update(a.arg for a in node.args.kwonlyargs)
    sinks = {"code-injection", "command-injection", "sql-injection",
             "path-traversal", "ssrf", "deserialization"}
    if params and sinks & set(found) \
            and not any(t in code for t in _VALIDATE_TOKENS):
        add("unvalidated-input")
    if params & _AUTH_PARAMS \
            and not any(t.lower() in code.lower() for t in _AUTH_TOKENS):
        add("auth-gap")
    order = [d[0] for d in DETECTORS]
    return sorted(found, key=order.index)[:MAX_ITEMS]


def _detect_from_text(code: str) -> list[str]:
    """Regex fallback when the snippet does not parse: same ids, same order."""
    low = code.lower()
    hits: list[str] = []

    def add(item: str, cond: bool) -> None:
        if cond and item not in hits:
            hits.append(item)

    add("code-injection", bool(re.search(r"\beval\s*\(|\bexec\s*\(", code)))
    add("command-injection",
        "os.system" in low or "popen" in low or "subprocess" in low
        or "shell=true" in low)
    add("sql-injection", "execute" in low and ("%" in code or "format" in low))
    add("path-traversal", bool(re.search(r"\bopen\s*\(", code)))
    add("ssrf", "requests" in low or "urllib" in low or "httpx" in low)
    add("deserialization", "pickle.loads" in low or "yaml.load" in low
        or "marshal.loads" in low)
    add("hardcoded-secret", bool(_SECRET_RE.search(code)))
    add("broad-except", bool(re.search(r"except\s*:|except\s+Exception", code)))
    order = [d[0] for d in DETECTORS]
    return sorted(hits, key=order.index)[:MAX_ITEMS]


def _labels(ids: list[str]) -> list[str]:
    by_id = {d[0]: d[1] for d in DETECTORS}
    return [by_id[i] for i in ids if i in by_id]


def _keys(ids: list[str]) -> list[list[str]]:
    by_id = {d[0]: list(d[2]) for d in DETECTORS}
    return [by_id[i] for i in ids if i in by_id]


def _empty_card(ex_id, name, file, line, commit, code):
    """Ungrounded card for a snippet with no attack surface.

    The pipeline drops grounded=False cards, and test_all_types_generate
    requires every type to build a front — so "nothing to threat-model"
    is a card, never None. Grading stays fail-closed (no checklist).
    """
    front = (f"Threat-model `{name}`: list its abuse cases, one per line.\n"
             f"```python\n{code[:CODE_LIMIT]}\n```\n"
             "Static analysis found no attack surface here (no sinks, "
             "secrets, auth-relevant parameters, or broad handlers) — "
             "this card is skipped in lesson modules.")
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": name,
        "concept": name, "file": file, "line": line, "commit": commit,
        "hints": ["No sinks, no secrets, no auth parameters: nothing to list.",
                  "Compare with a function that calls eval, open, or os.system.",
                  "Recognizing safe code is the skill — then move on."],
        "front": front, "back": "No attack surface found.",
        "payload": {"items": [], "keys": [], "solution": [],
                    "surface": [], "grounded": False},
    }


def generate(ex_id, concept, snippet, ctx):
    """Build a threat-model checklist card (never raises, never None).

    No analysable attack surface (or analysis failure) yields an
    ungrounded card the pipeline drops — never None, so the
    all-types-generate contract holds for every snippet.
    """
    try:
        ctx = ctx or {}
        name = _concept_field(concept, "name", "function") or "function"
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        code = _code_of(snippet)[:4000]
        if not code.strip():
            return _empty_card(ex_id, name, file, line, commit, code)
        tree = _tree(code)
        ids = (_detect_from_tree(code, tree) if tree is not None
               else _detect_from_text(code))
        if not ids:
            return _empty_card(ex_id, name, file, line, commit, code)
        items = _labels(ids)
        front = (f"Threat-model `{name}`: list its abuse cases "
                 f"({len(items)} threat-model items, one per line).\n"
                 f"```python\n{code[:CODE_LIMIT]}\n```")
        back = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(items))
        hints = [
            "Follow untrusted input to dangerous sinks: eval, shell, SQL, URLs, files.",
            "Check each parameter: is it validated, and is anyone's permission checked?",
            "Secrets and broad excepts count too — hardcoded keys and hidden failures.",
        ]
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": hints, "front": front, "back": back,
            "payload": {"items": items, "keys": _keys(ids),
                        "solution": items, "surface": ids,
                        "grounded": True},
        }
    except Exception:  # never raise, never None: ungrounded card
        try:
            return _empty_card(ex_id, "function", "", 0, "", "")
        except Exception:  # noqa: BLE001 -- absolute last resort
            return {"id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
                    "bloom": BLOOM, "front": "Threat-model this function.",
                    "back": "No attack surface found.",
                    "payload": {"items": [], "grounded": False}}


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _fold(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", str(text).lower())


def _tokens(text: str) -> set[str]:
    return {w for w in _fold(text).split() if len(w) > 2}


def _hit(label: str, keys: list[str], blob: str, toks: set[str]) -> bool:
    folded = _fold(label)
    if folded and folded in blob:
        return True
    if any(k and _fold(k) in blob for k in keys):
        return True
    lt = _tokens(label)
    if lt and len(lt & toks) / len(lt) >= 0.5:
        return True
    return False


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Checklist match: partial credit per item, fail closed. Never raises."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {})
        items = list(payload.get("items", []) or [])
        keys = list(payload.get("keys", []) or [])
        if not items:
            return _fail("Exercise payload is missing the checklist.")
        text = str(submission if submission is not None else "").strip()
        if not text:
            return _fail("List at least one abuse case, one per line "
                         f"(this function has {len(items)}).")
        blob = _fold(text)
        toks = _tokens(text)
        missed: list[str] = []
        for i, label in enumerate(items):
            ks = list(keys[i]) if i < len(keys) and keys[i] else []
            if not _hit(str(label), [str(k) for k in ks], blob, toks):
                missed.append(str(label))
        got = len(items) - len(missed)
        score = got / len(items)
        if got == len(items):
            return {"pass": True, "score": 1.0,
                    "feedback": f"Full threat model ({got}/{len(items)} items)."}
        ok = score >= 0.5
        detail = (f"Matched {got}/{len(items)} items."
                  + ("" if ok else " Need at least half to pass.")
                  + f" Missing: {'; '.join(missed)[:200]}")
        return {"pass": ok, "score": score, "feedback": detail}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — list abuse cases, one per line.")


def render(exercise: dict) -> str:
    """Function code + checklist textarea widget (rollback shape)."""
    payload = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    n = len(payload.get("items", []))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Checklist match — name at least half of the "
        f"{n} abuse cases (spelling/punctuation-folded, partial credit "
        f"per item). No sandbox.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='6' cols='70' "
        f"placeholder='One abuse case per line ({n} to find)'></textarea><br>"
        f"<button>Check threat model</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Threat modelling <small>(feature)</small></h3>"
        "<p>Read a function and list its abuse cases — injection surfaces, "
        "unvalidated inputs, auth gaps, hardcoded secrets — graded against "
        "a statically derived checklist with per-item partial credit, "
        "no sandbox. "
        "<code>groundwork/threatmodel.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "threat-model", "kind": "feature",
            "title": "Threat modelling",
            "blurb": "List a function's abuse cases — injections, auth gaps, secrets.",
            "path": "/status", "anchor": "status-b9-threatmodel"}
