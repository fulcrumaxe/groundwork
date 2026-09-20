"""Registry-driven docs: README sections + docs/ grow with the tour registry.

`python -m groundwork docs` rewrites the generated sections in place;
`python -m groundwork docs --check` (and CI) fails when they are stale,
so every shipped feature/improvement lands in the docs with zero
separate effort.
"""
from __future__ import annotations

from pathlib import Path

from . import tour as tourmod

ROOT = Path(__file__).resolve().parent.parent

KINDS = (("feature", "Features"), ("improvement", "Improvements"),
         ("mvp", "The original loop"))


def _target(e: dict) -> str:
    path = e["path"].replace("{mid}", "&lt;id&gt;").replace(
        "{lesson}", "&lt;lesson&gt;")
    return f"{path}#{e['anchor']}"


def catalog_rows(kind: str) -> list[str]:
    return [f"| {e['title']} | {e['blurb']} | `{_target(e)}` |"
            for e in tourmod.ENTRIES if e["kind"] == kind]


def features_doc() -> str:
    parts = ["# Feature catalog",
             "",
             "Generated from the tour registry — do not edit by hand. "
             "Run `python -m groundwork docs` to refresh.",
             ""]
    for kind, heading in KINDS:
        parts += [f"## {heading}", "",
                  "| Capability | What it does | Where |",
                  "|---|---|---|"] + catalog_rows(kind) + [""]
    return "\n".join(parts)


def readme_table(kind: str) -> str:
    return "\n".join(["| Capability | What it does | Where |",
                      "|---|---|---|"] + catalog_rows(kind))


def _swap(text: str, marker: str, body: str) -> str:
    start = f"<!-- GW-{marker}:START -->"
    end = f"<!-- GW-{marker}:END -->"
    pre, sep, rest = text.partition(start)
    if not sep:
        raise KeyError(f"README marker missing: {marker}")
    _, sep2, post = rest.partition(end)
    if not sep2:
        raise KeyError(f"README end marker missing: {marker}")
    return f"{pre}{start}\n{body}\n{end}{post}"


def render_all() -> list[str]:
    """Rewrite generated docs; return paths whose bytes changed."""
    changed = []
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    new = _swap(text, "FEATURES", readme_table("feature"))
    new = _swap(new, "IMPROVEMENTS", readme_table("improvement"))
    if new != text:
        readme.write_text(new, encoding="utf-8")
        changed.append("README.md")
    doc = ROOT / "docs" / "features.md"
    body = features_doc()
    old = doc.read_text(encoding="utf-8") if doc.exists() else None
    if old != body:
        doc.parent.mkdir(exist_ok=True)
        doc.write_text(body, encoding="utf-8")
        changed.append("docs/features.md")
    return changed
