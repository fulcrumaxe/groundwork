"""Tiny dependency-free Python/TS syntax highlighter (I-62).

Single-pass tokenizer plus escape-first renderer for status-page code
snippets. Python and TypeScript only; everything else fails closed to
plain text. No dependencies, no network, no I/O: `re` and `html` from
the stdlib. The parent owns head wiring (`highlight_css()` returns raw
declarations, never <style> tags) and page assembly (`section_html()`
is db-free, like the batch8/batch9 sections).
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b10-highlight"

KINDS = ("comment", "string", "number", "keyword", "builtin", "plain")

_PY_KEYWORDS = frozenset({
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "case", "class", "continue", "def", "del", "elif", "else",
    "except", "finally", "for", "from", "global", "if", "import", "in",
    "is", "lambda", "match", "nonlocal", "not", "or", "pass", "raise",
    "return", "try", "while", "with", "yield",
})

_TS_KEYWORDS = frozenset({
    "abstract", "any", "as", "async", "await", "bigint", "boolean", "break",
    "case", "catch", "class", "const", "continue", "debugger", "declare",
    "default", "delete", "do", "else", "enum", "export", "extends", "false",
    "finally", "for", "from", "function", "if", "implements", "import", "in",
    "instanceof", "interface", "let", "namespace", "never", "new", "null",
    "number", "object", "of", "private", "protected", "public", "readonly",
    "return", "satisfies", "static", "string", "super", "switch", "symbol",
    "this", "throw", "true", "try", "type", "typeof", "undefined", "unknown",
    "var", "void", "while", "with", "yield",
})

_PY_BUILTINS = frozenset({
    "AttributeError", "Exception", "IndexError", "KeyError", "StopIteration",
    "TypeError", "ValueError", "bool", "cls", "dict", "float", "int",
    "isinstance", "issubclass", "len", "list", "object", "print", "range",
    "repr", "self", "set", "str", "super", "tuple", "type",
})

_TS_BUILTINS = frozenset({
    "Array", "Boolean", "Date", "Error", "Infinity", "JSON", "Map", "Math",
    "NaN", "Number", "Object", "Promise", "RegExp", "Set", "String",
    "Symbol", "console", "document", "parseFloat", "parseInt", "window",
})

_LANGS = {"python": "python", "py": "python",
          "ts": "ts", "typescript": "ts"}

_CLASS = {"comment": "tok-comment", "string": "tok-string",
          "number": "tok-number", "keyword": "tok-keyword",
          "builtin": "tok-builtin"}

_WORD_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_NUM_RE = re.compile(
    r"0[xX][0-9a-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+"
    r"|(?:\d[\d_]*)(?:\.[\d_]*)?(?:[eE][+-]?[\d_]+)?|\.[\d_]+")
_PY_PREFIX_RE = re.compile(r"(?i)(?:rb|br|fr|rf|[rbf])?(?='''|\"\"\"|'|\")")


def _norm_lang(lang) -> str:
    """Normalize to 'python'/'ts'; anything else fails closed to ''."""
    try:
        return _LANGS.get(str(lang).strip().lower(), "")
    except Exception:  # noqa: BLE001 — lookup must never raise
        return ""


def _read_str(text: str, i: int, prefix: str, quote: str) -> int:
    """End offset just past the string starting at i (prefix + quote)."""
    n = len(text)
    raw = prefix.lower().startswith("r")
    j = i + len(prefix) + len(quote)
    if len(quote) == 3:
        end = text.find(quote, j)
        if end == -1:  # unterminated: consume to end, still a string
            return n
        return end + 3
    while j < n:
        ch = text[j]
        if not raw and ch == "\\":
            j += 2
            continue
        if ch == quote:
            return j + 1
        if ch == "\n":  # single-quoted: newline ends it, still a string
            return j
        j += 1
    return n


def _scan(text: str, lang: str):
    """Yield (kind, chunk); single left-to-right pass, spans never overlap."""
    i, n, plain = 0, len(text), []

    def flush():
        if plain:
            yield ("plain", "".join(plain))
            plain.clear()

    while i < n:
        ch = text[i]
        if lang == "python" and ch == "#":
            j = text.find("\n", i)
            if j == -1:
                j = n
            yield from flush()
            yield ("comment", text[i:j])
            i = j
            continue
        if lang == "ts" and text.startswith("//", i):
            j = text.find("\n", i)
            if j == -1:
                j = n
            yield from flush()
            yield ("comment", text[i:j])
            i = j
            continue
        if lang == "ts" and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j == -1 else j + 2  # unclosed: to end, still a comment
            yield from flush()
            yield ("comment", text[i:j])
            i = j
            continue
        quote = None
        prefix = ""
        if lang == "python":
            m = _PY_PREFIX_RE.match(text, i)
            if m and m.group(0):
                prefix = m.group(0)
            rest = text[i + len(prefix):i + len(prefix) + 3]
            for q in ("'''", '"""', "'", '"'):
                if rest.startswith(q):
                    quote = q
                    break
        else:
            if ch in "'\"`":
                quote = ch
        if quote is not None:
            yield from flush()
            j = _read_str(text, i, prefix, quote)
            yield ("string", text[i:j])
            i = j
            continue
        m = _NUM_RE.match(text, i) if ch.isdigit() or (
                ch == "." and i + 1 < n and text[i + 1].isdigit()) else None
        if m:
            yield from flush()
            yield ("number", m.group(0))
            i = m.end()
            continue
        m = _WORD_RE.match(text, i)
        if m:
            word = m.group(0)
            yield from flush()
            if lang == "python":
                kind = ("keyword" if word in _PY_KEYWORDS
                        else "builtin" if word in _PY_BUILTINS else "plain")
            else:
                kind = ("keyword" if word in _TS_KEYWORDS
                        else "builtin" if word in _TS_BUILTINS else "plain")
            yield (kind, word)
            i = m.end()
            continue
        plain.append(ch)
        i += 1
    yield from flush()


def tokenize(code, lang="python") -> list:
    """Split code into [(kind, text)] tokens; never raises.

    Unknown/empty langs and non-string input fail closed: a single
    ("plain", text) token, always renderable. Joining every chunk
    reproduces the input exactly (lossless).
    """
    try:
        text = code if isinstance(code, str) else str(code)
        norm = _norm_lang(lang)
        if not norm or not text:
            return [("plain", text)]
        return list(_scan(text, norm)) or [("plain", text)]
    except Exception:  # noqa: BLE001 — tokenizer must never raise
        try:
            return [("plain", str(code))]
        except Exception:  # noqa: BLE001 — last resort, still no raise
            return [("plain", "")]


def highlight_html(code, lang="python") -> str:
    """Render code as <pre class='hl'><code> with tok-* spans.

    Escape-first: each token's RAW text goes through html.escape BEFORE
    any span markup is added, so the output provably contains none of
    the input's raw <, >, or &. Never raises (fail-closed plain block).
    """
    try:
        parts = []
        for kind, chunk in tokenize(code, lang):
            esc = html.escape(chunk, quote=True)
            cls = _CLASS.get(kind)
            parts.append(f"<span class='{cls}'>{esc}</span>"
                         if cls else esc)
        return "<pre class='hl'><code>" + "".join(parts) + "</code></pre>"
    except Exception:  # noqa: BLE001 — renderer must never raise
        try:
            safe = html.escape(str(code), quote=True)
        except Exception:  # noqa: BLE001 — last resort, still no raise
            safe = ""
        return "<pre class='hl'><code>" + safe + "</code></pre>"


def highlight_css() -> str:
    """Raw CSS declarations only — never <style> tags (parent wires head).

    Base token colors read on the light palette; the
    prefers-color-scheme block re-assigns just the token colors for the
    dark palette. No font-family (fontstack.py owns that).
    """
    return (
        ".hl{overflow-x:auto;border-radius:4px;padding:8px 10px}"
        ".hl .tok-keyword{color:#7c3aed;font-weight:600}"
        ".hl .tok-string{color:#1a7f37}"
        ".hl .tok-comment{color:#6e7781;font-style:italic}"
        ".hl .tok-number{color:#b45309}"
        ".hl .tok-builtin{color:#087990}"
        "@media (prefers-color-scheme:dark){"
        ".hl .tok-keyword{color:#c4b5fd}"
        ".hl .tok-string{color:#7ee787}"
        ".hl .tok-comment{color:#9aa4b2}"
        ".hl .tok-number{color:#fbbf24}"
        ".hl .tok-builtin{color:#79c0ff}}"
    )


_DEMO = "def greet(name='world'):\n    return f'hi {name}'  # say hi"


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Tiny syntax highlight "
        "<small>(improvement)</small></h3>"
        "<p>Python and TypeScript snippets get lightweight coloring with no "
        "dependencies: <code>groundwork/highlight.py</code> provides "
        "<code>tokenize()</code> (single-pass scanner; unknown languages "
        "fail closed to plain text, never raises), "
        "<code>highlight_html()</code> (escapes raw text before wrapping "
        "tokens in <code>tok-*</code> spans, so markup can never leak), and "
        "<code>highlight_css()</code> (raw declarations plus a dark-mode "
        "re-color, no <code>&lt;style&gt;</code> tags).</p>"
        + highlight_html(_DEMO, "python")
    )
