"""Distinguish external vs internal links visually (I-31).

Classifies hrefs (internal route vs external URL vs repo path) and
decorates only external links: merges ``class="ext-link"`` and
``rel="noopener"`` (preserving existing tokens) and appends a
CSS corner-arrow marker plus a visually-hidden "(external link)" note.

Pure functions, stdlib only (``html``/``re``), import-safe standalone:
no groundwork imports, no I/O, no DB/schema changes, no web.py edits.
Complements ``levelcarry`` (which skips externals) and ``copylink``
(which owns ``#anchor`` shape); neither behavior is altered here.
"""
from __future__ import annotations

import html
import re

MARKER = (
    ' <span class="ext-marker" aria-hidden="true"></span>'
    '<span class="visually-hidden">(external link)</span>'
)

_A_FULL_RE = re.compile(
    r"<a\b(?P<attrs>[^>]*?)>(?P<body>.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
# Well-formed href attribute only: whitespace before the name, no quote
# characters inside the value (so hostile injections such as
# missing-space attribute smuggling can never match through
# backtracking), and whitespace / / > right after the closing quote.
# The search runs on the opening tag *including* its ">", because the
# attrs capture excludes it. Unquoted URLs never match and pass through.
_HREF_RE = re.compile(
    r"""(?<=\s)href=(?:"(?P<href_d>[^"]*)"|'(?P<href_s>[^']*)')(?=[\s>/])""",
    re.IGNORECASE,
)
_CLASS_RE = re.compile(r"""\bclass=(['"])(?P<val>.*?)\1""", re.IGNORECASE)
_REL_RE = re.compile(r"""\brel=(['"])(?P<val>.*?)\1""", re.IGNORECASE)

_SKIP_PREFIXES = ("#", "mailto:", "tel:", "data:", "javascript:")
_EXTERNAL_PREFIXES = ("http://", "https://", "//")
_REPO_PREFIXES = ("groundwork/", "tests/", "static/", "docs/",
                  "./", "../")


def _str(href) -> str | None:
    return href if isinstance(href, str) else None


def classify(href) -> str:
    """One of 'external' | 'internal' | 'repo' | 'skip'.

    skip: non-string, empty/whitespace, #fragment, mailto:/tel:/
    data:/javascript:. external: http(s):// or protocol-relative //.
    repo: repo-relative source path (known top dirs or a .py file
    target, query/fragment stripped). internal: everything else
    (absolute routes like /status, relative hrefs like lessons/intro).
    """
    s = _str(href)
    if s is None:
        return "skip"
    t = s.strip()
    if not t:
        return "skip"
    low = t.lower()
    if low.startswith(_SKIP_PREFIXES):
        return "skip"
    if low.startswith(_EXTERNAL_PREFIXES):
        return "external"
    head = t.split("#", 1)[0].split("?", 1)[0].strip()
    low_head = head.lower()
    if (low_head.startswith(_REPO_PREFIXES)
            or low_head.endswith(".py")
            or "/groundwork/" in low_head
            or "/tests/" in low_head):
        return "repo"
    return "internal"


def is_external(href) -> bool:
    """True only for external URLs (http/https/protocol-relative)."""
    return classify(href) == "external"


def _merge_attr(attrs: str, kind: str) -> str:
    """Merge ext-link decoration into one <a> attr string."""
    if kind == "class":
        m = _CLASS_RE.search(attrs)
        if m is None:
            return f'{attrs} class="ext-link"'
        tokens = m.group("val").split()
        if "ext-link" not in tokens:
            tokens.append("ext-link")
        return _CLASS_RE.sub(
            lambda _: f'class="{html.escape(" ".join(tokens), quote=True)}"',
            attrs, count=1)
    m = _REL_RE.search(attrs)
    if m is None:
        return f'{attrs} rel="noopener"'
    tokens = m.group("val").split()
    if "noopener" not in [t.lower() for t in tokens]:
        tokens.append("noopener")
    return _REL_RE.sub(
        lambda _: f'rel="{html.escape(" ".join(tokens), quote=True)}"',
        attrs, count=1)


def decorate(html_text) -> str:
    """Append marker + class/rel to external <a> links only.

    Non-external anchors (internal routes, repo paths, fragments,
    mailto:, tags with unquoted/hostile hrefs) are returned
    byte-identical; already-decorated links are never doubled.
    Non-string input passes through unchanged.
    """
    if not isinstance(html_text, str) or "href=" not in html_text:
        return html_text

    def _one(m: "re.Match") -> str:
        attrs, body = m.group("attrs"), m.group("body")
        tag = m.group(0).split(">", 1)[0] + ">"
        hm = _HREF_RE.search(tag)
        if hm is None:
            return m.group(0)
        href = hm.group("href_d")
        if href is None:
            href = hm.group("href_s")
        if not is_external(href):
            return m.group(0)
        if "ext-marker" in body:
            return m.group(0)
        attrs = _merge_attr(_merge_attr(attrs, "class"), "rel")
        return f"<a{attrs}>{body}{MARKER}</a>"

    return _A_FULL_RE.sub(_one, html_text)


def demo() -> str:
    """Escaped decorate() sample for the Status section."""
    return html.escape(decorate("<a href='https://example.com/x'>Docs</a>"))


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b8-extlinks'>External-link distinction "
        "<small>(improvement)</small></h3>"
        "<p>External links carry <code>class='ext-link'</code>, "
        "<code>rel='noopener'</code>, and a CSS corner-arrow marker with a "
        "visually-hidden “(external link)” note; internal routes and repo "
        f"paths are untouched (e.g. <code>{demo()}</code>). "
        "<code>groundwork/extlinks.py</code>.</p>"
    )
