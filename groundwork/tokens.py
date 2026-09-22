"""Design-token table for contributors (I-94).

One TOKENS table is the single source for the README design-tokens
section and the styleguide gallery rows, so the two can never drift:
values are read from the real `palette`/`radius` emitters (never
copied), and a renamed token breaks the parity test instead of
silently desyncing docs. Later scales (spacing, type, fonts) join by
appending rows, never by scraping docstrings. Pure functions, stdlib
only (html), no I/O, no DB changes.
"""
from __future__ import annotations

import html

from . import palette as palettemod
from . import radius as radiusmod

STATUS_ANCHOR = "status-b18-tokens"

_USAGE = {
    "--ink": "Body text and headings on paper surfaces.",
    "--paper": "Page background; pairs with --ink for body text.",
    "--accent-due": "Due-queue accent; doubles as the pass color.",
    "--accent-modules": "Modules-library accent.",
    "--accent-history": "History-page accent.",
    "--pass": "Pass verdicts and owned states.",
    "--fail": "Fail verdicts and destructive emphasis.",
    "--stale": "Muted chrome: stale chips, scrollbars, borders.",
    "--r-card": "Card corners: articles, module cards, banners.",
    "--r-control": "Control corners: buttons, inputs, code blocks.",
    "--r-chip": "Pill corners: chips, confidence pills, back-to-top.",
}


def _emitter_tokens() -> list:
    """Name/value pairs straight from the real emitters; never raises."""
    try:
        pairs = list(palettemod.PALETTE.items()) + \
            list(radiusmod.RADII.items())
        return [{"name": str(k), "value": str(v),
                 "usage": _USAGE.get(str(k), "")}
                for k, v in pairs]
    except Exception:  # noqa: BLE001 — emitter read must never raise
        return []


TOKENS = _emitter_tokens()


def _rows(tokens=None) -> list:
    if tokens is None:
        tokens = TOKENS
    if not isinstance(tokens, (list, tuple)):
        return []
    out = [t for t in tokens if isinstance(t, dict)
           and t.get("name") and t.get("value")]
    return sorted(out, key=lambda t: str(t["name"]))


def readme_section(tokens=None) -> str:
    """README design-tokens section: markdown table for docs regen."""
    rows = _rows(tokens)
    if not rows:
        return ("| Name | Value | Usage |\n|---|---|---|\n"
                "| (no tokens) | — | Token table is empty. |")
    lines = ["| Name | Value | Usage |", "|---|---|---|"]
    for t in rows:
        lines.append(f"| `{t['name']}` | `{t['value']}` "
                     f"| {t.get('usage', '')} |")
    return "\n".join(lines)


def styleguide_rows(tokens=None) -> str:
    """Gallery rows: one live row per token with a color swatch."""
    rows = _rows(tokens)
    if not rows:
        return ("<h2>Design tokens</h2><p>No tokens registered — "
                "see <code>groundwork/tokens.py</code>.</p>")
    parts = ["<h2>Design tokens</h2><table class='log'>"
             "<tr><th>Token</th><th>Swatch</th><th>Value</th>"
             "<th>Usage</th></tr>"]
    for t in rows:
        name = html.escape(str(t["name"]))
        value = html.escape(str(t["value"]))
        usage = html.escape(str(t.get("usage", "")))
        parts.append(
            f"<tr><td><code>{name}</code></td>"
            f"<td><span style='display:inline-block;width:1.2em;"
            f"height:1.2em;background:{value};"
            "border:1px solid var(--stale)'></span></td>"
            f"<td><code>{value}</code></td><td>{usage}</td></tr>")
    return "".join(parts) + "</table>"


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch18.py."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Design tokens "
        "<small>(improvement)</small></h3>"
        "<p>Contributors get one token table instead of scattered "
        "literals: <code>groundwork/tokens.py</code> owns "
        "<code>TOKENS</code> (name/value/usage, read from the real "
        "<code>palette</code>/<code>radius</code> emitters), "
        "<code>readme_section()</code> (the README design-tokens table "
        "consumed by docs regen), and <code>styleguide_rows()</code> "
        "(live gallery rows with swatches). Empty input renders a note, "
        "never raises.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "design-tokens",
        "kind": "improvement",
        "title": "Design tokens",
        "blurb": ("One token table documents every palette and radius "
                  "token in the README and the styleguide."),
        "path": "/status",
        "anchor": "status-b18-tokens",
    }
