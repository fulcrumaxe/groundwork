"""Design tokens: real palette as CSS variables (I-51).

Single source for ink, paper, three page accents, and
pass/fail/stale status colors. Emits a :root block so page CSS
can reference var(--ink) etc. instead of hardcoded hex values.
No DB changes.
"""
from __future__ import annotations

PALETTE = {
    "--ink": "#1a1a1a",
    "--paper": "#ffffff",
    "--accent-due": "#0b6e4f",
    "--accent-modules": "#8a5a00",
    "--accent-history": "#33507a",
    "--pass": "#0b6e4f",
    "--fail": "#a4262c",
    "--stale": "#6b6b6b",
}


def palette_css() -> str:
    """Return a :root block defining the site palette."""
    decls = "".join(f"{k}:{v};" for k, v in PALETTE.items())
    return f":root{{{decls}}}"
