"""Sticky TOC section highlight (I-6).

Builds on the lesson TOC rendered by web.module_html (the sticky
``<p class='toc' id='readtime'>`` paragraph, see web.py): same markup
plus data attributes, a tiny CSS rule, and an inline script that marks
the in-view section's link via IntersectionObserver (rAF-throttled
scroll fallback). Pure functions of strings/lists — no I/O, no DB
changes, stdlib only.
"""
from __future__ import annotations

import html
import re

TOC_ID = "readtime"
ACTIVE_CLASS = "active"
SCRIPT_MARKER = "data-toc-highlight"

_TOC_P_RE = re.compile(r"<p class='toc' id='readtime'>")
_LINK_RE = re.compile(r"<a href='#lesson-([^']+)'>(.*?)</a>")


def toc_link(slug, name, minutes) -> str:
    """One TOC link in web.py's shape, plus a data-toc-link hook."""
    s = slug if isinstance(slug, str) else ""
    label = name if isinstance(name, str) else ""
    try:
        mins = int(minutes)
    except (TypeError, ValueError):
        mins = 1
    safe = html.escape(s, quote=True)
    return (
        f"<a href='#lesson-{safe}' data-toc-link='lesson-{safe}'>"
        f"{html.escape(label)}</a> · {mins} min"
    )


def toc_html(entries) -> str:
    """Full sticky TOC paragraph from [(slug, name, minutes)] triples."""
    items = list(entries or [])
    if not items:
        return ""
    links = " · ".join(toc_link(s, n, m) for s, n, m in items)
    return (
        f"<p class='toc' id='{TOC_ID}' data-toc>"
        f"<small>In this module: {links}</small> "
        f"<small>(minutes per lesson)</small></p>"
    )


def _add_link_attr(match: re.Match) -> str:
    slug, label = match.group(1), match.group(2)
    if "data-toc-link" in match.group(0):
        return match.group(0)
    return (
        f"<a href='#lesson-{slug}' data-toc-link='lesson-{slug}'>"
        f"{label}</a>"
    )


def enhance_toc(paragraph) -> str:
    """Upgrade a legacy TOC paragraph (web.py's current markup).

    Adds the data-toc root hook, per-link data-toc-link targets, the
    highlight CSS and the observer script. Idempotent; non-TOC input
    passes through unchanged.
    """
    if not isinstance(paragraph, str):
        return ""
    if "data-toc" in paragraph or SCRIPT_MARKER in paragraph:
        return paragraph
    if "<p class='toc'" not in paragraph or "id='readtime'" not in paragraph:
        return paragraph
    out = _TOC_P_RE.sub(
        "<p class='toc' id='readtime' data-toc>", paragraph, count=1)
    out = _LINK_RE.sub(_add_link_attr, out)
    return out + style_css() + script_js()


def style_css() -> str:
    """Highlight rule for the in-view TOC link (mirrors nav active)."""
    return (
        "<style>p.toc#readtime a.active,p.toc#readtime a[aria-current]"
        "{background:#1a1a1a;color:#fff;border-radius:6px;"
        "padding:.05rem .4rem;text-decoration:none}</style>"
    )


def script_js() -> str:
    """Inline observer: toggles .active + aria-current on the visible link."""
    return (
        "<script " + SCRIPT_MARKER + ">\n"
        "(function () {\n"
        "  var toc = document.querySelector(\"p.toc#readtime[data-toc]\");\n"
        "  if (!toc) return;\n"
        "  var links = Array.prototype.slice.call(\n"
        "    toc.querySelectorAll(\"a[data-toc-link]\"));\n"
        "  if (!links.length) return;\n"
        "  function setActive(id) {\n"
        "    links.forEach(function (a) {\n"
        "      var on = a.getAttribute(\"data-toc-link\") === id;\n"
        "      if (on) { a.classList.add(\"active\");\n"
        "        a.setAttribute(\"aria-current\", \"true\"); }\n"
        "      else { a.classList.remove(\"active\");\n"
        "        a.removeAttribute(\"aria-current\"); }\n"
        "    });\n"
        "  }\n"
        "  var sections = links.map(function (a) {\n"
        "    return document.getElementById(a.getAttribute(\"data-toc-link\"));\n"
        "  }).filter(Boolean);\n"
        "  if (\"IntersectionObserver\" in window) {\n"
        "    var current = null;\n"
        "    var obs = new IntersectionObserver(function (entries) {\n"
        "      entries.forEach(function (en) {\n"
        "        if (en.isIntersecting) current = en.target.id;\n"
        "      });\n"
        "      if (current) setActive(current);\n"
        "    }, {rootMargin: \"-30% 0px -60% 0px\"});\n"
        "    sections.forEach(function (s) { obs.observe(s); });\n"
        "  } else {\n"
        "    var ticking = false;\n"
        "    window.addEventListener(\"scroll\", function () {\n"
        "      if (ticking) return; ticking = true;\n"
        "      requestAnimationFrame(function () {\n"
        "        ticking = false;\n"
        "        var pos = window.scrollY + window.innerHeight * 0.3;\n"
        "        var id = null;\n"
        "        sections.forEach(function (s) {\n"
        "          if (s.offsetTop <= pos) id = s.id;\n"
        "        });\n"
        "        if (id) setActive(id);\n"
        "      });\n"
        "    }, {passive: true});\n"
        "  }\n"
        "})();\n"
        "</script>"
    )


def active_for(position, offsets):
    """Pure mirror of the scroll fallback: slug of the section in view.

    offsets: ordered [(section_id, top_px)] pairs. Returns the last
    section whose top is at/above position, else None.
    """
    try:
        pos = float(position)
    except (TypeError, ValueError):
        return None
    if not isinstance(offsets, (list, tuple)) or not offsets:
        return None
    current = None
    for slug, top in offsets:
        try:
            t = float(top)
        except (TypeError, ValueError):
            continue
        if t <= pos:
            current = slug
    return current


def status_html() -> str:
    """Status-page home for this item (anchor id status-b6-tochighlight)."""
    return (
        "<h3 id='status-b6-tochighlight'>Sticky TOC highlight"
        " <small>(improvement)</small></h3>"
        "<p>The sticky module TOC marks the section currently in view — "
        "IntersectionObserver with a scroll fallback, reduced-motion safe "
        "(class toggle only, no animated scrolling). "
        "<code>groundwork/tochighlight.py</code>.</p>"
    )
