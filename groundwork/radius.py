"""Border-radius scale: one token source for all corner radii (I-67).

Cards take --r-card (12px), controls take --r-control (8px), chips
take --r-chip (999px). radius_css() emits a :root block so page CSS
references var(--r-*) instead of hardcoded literals; token_for()
maps each legacy literal to its token so migration is mechanical.
Hairline accents (4px bars/kbd, 2px ladder ticks) are outside the
scale and stay literal. No DB changes.
"""
from __future__ import annotations

RADII = {
    "--r-card": "12px",
    "--r-control": "8px",
    "--r-chip": "999px",
}

# Legacy literal -> token var, from the web.py CSS audit (I-67):
# 10px on article/.modcard/.tour-banner/#shortcuts -> card;
# 6px on pre/button/inputs/nav-a/parsons-li/a.btn -> control;
# 999px on .chip/.conf/a.totop -> chip.
LEGACY_MAP = {
    "10px": "var(--r-card)",
    "6px": "var(--r-control)",
    "999px": "var(--r-chip)",
}

STATUS_ANCHOR = "status-b11-radius"


def radius_css() -> str:
    """Return a :root block defining the radius scale."""
    decls = "".join(f"{k}:{v};" for k, v in RADII.items())
    return f":root{{{decls}}}"


def token_for(value) -> str:
    """Var reference for a legacy radius literal; "" when out of scale.

    "10px" -> var(--r-card), "6px" -> var(--r-control),
    "999px" -> var(--r-chip). Anything else (4px/2px hairlines,
    unknown, empty, non-string) returns "" so the caller keeps the
    literal; never raises.
    """
    try:
        hit = LEGACY_MAP.get(str(value).strip())
        return hit if isinstance(hit, str) else ""
    except Exception:  # noqa: BLE001 - audit helper never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Corner radii <small>(improvement)</small></h3>"
        "<p>Cards round at 12px, controls at 8px, chips pill at 999px — "
        "one <code>:root</code> source instead of scattered 10px/6px/999px "
        "literals. <code>groundwork/radius.py</code> provides "
        "<code>RADII</code> (the three tokens), <code>radius_css()</code> "
        "(:root emitter, palette.py pattern), and <code>token_for()</code> "
        "(legacy-literal audit lookup that returns \"\" for out-of-scale "
        "hairlines and never raises).</p>"
    )
