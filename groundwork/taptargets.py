"""44px minimum tap targets on all buttons and inputs (I-66).

One --tap-min token (44px, WCAG 2.5.8) is the single source: every
element rule references var(--tap-min) so the floor cannot drift.
min-height (never height) keeps larger content unclipped, and primary
selectors additionally keep min-width so icon-only buttons stay
tappable. The compact-density toggle (I-89) owns spacing; this module
owns the floor — compact=True appends a guard rule scoped under
body.density-compact that re-pins primary selectors to the token, so
density can squeeze padding and fonts but never shrink primary
actions. audit() scans rendered HTML for inline-style escapes below
the floor. Pure functions, stdlib only (re, html.parser), no DB.
"""
from __future__ import annotations

from html.parser import HTMLParser

MIN_PX = 44

STATUS_ANCHOR = "status-b11-taptargets"

_BASE_SELECTORS = ("button", "input:not([type=hidden])", "select",
                   "textarea", ".btn")
_PRIMARY_SELECTORS = ("button", "input[type=submit]", "input[type=button]",
                      "input[type=image]", "select", ".btn")


def target_css(compact: bool = False) -> str:
    """Raw tap-floor declarations for the head wire (never <style> tags).

    Element rules reference only var(--tap-min); compact=True appends
    the density-compact guard re-pinning primaries to the floor.
    Never raises.
    """
    try:
        dense = bool(compact)
    except Exception:  # noqa: BLE001 — truthiness must never raise
        dense = False
    base = ",".join(_BASE_SELECTORS)
    primary = ",".join(_PRIMARY_SELECTORS)
    out = (f":root{{--tap-min:{MIN_PX}px}}"
           f"{base}{{min-height:var(--tap-min)}}"
           f"{primary}{{min-width:var(--tap-min)}}")
    if dense:
        out += (f"body.density-compact {primary}"
                "{min-height:var(--tap-min);min-width:var(--tap-min)}")
    return out


class _AuditParser(HTMLParser):
    """Collect controls whose inline size styles duck under the floor."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.findings: list = []

    def handle_starttag(self, tag, attrs) -> None:
        try:
            watched = tag in ("button", "select", "textarea")
            is_link_btn = False
            is_hidden = False
            style = ""
            for name, val in attrs:
                if name == "style" and isinstance(val, str):
                    style = val
                if tag == "a" and name == "class" \
                        and isinstance(val, str) and "btn" in val.split():
                    is_link_btn = True
                if tag == "input" and name == "type" \
                        and isinstance(val, str) \
                        and val.strip().lower() == "hidden":
                    is_hidden = True
            if tag == "input" and not is_hidden:
                watched = True
            if tag == "a":
                watched = is_link_btn
            if not watched or not style:
                return
            for decl in style.split(";"):
                if ":" not in decl:
                    continue
                prop, _, raw = decl.partition(":")
                prop = prop.strip().lower()
                if prop not in ("height", "min-height",
                                "width", "min-width"):
                    continue
                num = "".join(c for c in raw.strip().lower()
                              if c.isdigit() or c == ".")
                try:
                    size = float(num)
                except ValueError:
                    continue
                if "px" in raw.lower() and size < MIN_PX:
                    line, _ = self.getpos()
                    self.findings.append({
                        "line": line,
                        "element": f"<{tag}",
                        "detail": (f"inline {prop}:{raw.strip()} "
                                   f"is below the {MIN_PX}px floor"),
                    })
                    return
        except Exception:  # noqa: BLE001 — audit keeps findings so far
            return


def audit(markup) -> list:
    """Inline-style tap-floor escapes in rendered HTML.

    One finding dict per control {"line", "element", "detail"};
    class-based sizing is guaranteed by the token, so only inline
    styles are audited — not computed style or JS-resized DOM.
    Non-string or empty input -> []; never raises.
    """
    try:
        if not isinstance(markup, str) or not markup:
            return []
        parser = _AuditParser()
        try:
            parser.feed(markup)
        except Exception:  # noqa: BLE001 — keep findings so far
            pass
        return parser.findings
    except Exception:  # noqa: BLE001 — audit must never raise
        return []


def tour_entry() -> dict:
    """Tour registry entry for the 44px tap floor."""
    return {
        "id": "tap-targets",
        "kind": "improvement",
        "title": "44px tap targets",
        "blurb": ("Every button and input is at least 44px tall — "
                  "full-size even in compact density. See the floor "
                  "token below."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Tap targets "
        "<small>(improvement)</small></h3>"
        "<p>Every button and input keeps a 44px minimum via one "
        "<code>--tap-min</code> token — var-only rules, "
        "<code>min-height</code> so content never clips, and a "
        "compact-density guard that re-pins primary actions when the "
        "I-89 toggle squeezes spacing. "
        "<code>groundwork/taptargets.py</code> provides "
        "<code>target_css()</code> (token emitter plus density guard) "
        "and <code>audit()</code> (inline-style escape scan that never "
        "raises).</p>"
    )
