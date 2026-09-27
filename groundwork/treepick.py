"""Repo tree picker for where-live cards with many files (I-180).

Where-live (etype 4) asks which file owns a symbol and grades exact
file-text equality (exercises.grade t==4). cards.answer_widget renders
one submit button per choice, which scans fine for the usual four
files but turns into a mis-click wall once the list grows. Past
THRESHOLD choices this module renders a directory-grouped picker --
one <details> per directory, one radio per file -- posting the same
`answer` field, so grading and disclosures do not change. Short lists
keep the legacy buttons byte-identical. Pure functions, stdlib only.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b27-treepick"
ETYPE = "4"
THRESHOLD = 6  # more choices than this stop scanning as flat buttons


def _norm(path) -> str:
    """Repo-relative path, slashes only; "" when unusable."""
    if not isinstance(path, str):
        return ""
    cleaned = path.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned.strip("/")


def clean_choices(raw) -> list:
    """Normalized non-empty string choices, deduped, order kept."""
    try:
        items = list(raw) if isinstance(raw, (list, tuple)) else []
    except TypeError:
        return []
    out = []
    for c in items:
        n = _norm(c)
        if n and n not in out:
            out.append(n)
    return out


def should_pick(raw) -> bool:
    """True when the choice list is long enough to need the picker."""
    try:
        return len(clean_choices(raw)) > THRESHOLD
    except Exception:  # noqa: BLE001 -- fail closed to buttons
        return False


def group_by_dir(choices) -> list:
    """Sorted [(dir, [full paths])]; root files group under ""."""
    groups: dict = {}
    for c in clean_choices(choices):
        d, _, _ = c.rpartition("/")
        groups.setdefault(d, []).append(c)
    return sorted((d, sorted(fs)) for d, fs in groups.items())


def legacy_html(choices) -> str:
    """Byte-exact cards.py where-live button join (the fallback)."""
    try:
        items = list(choices) if isinstance(choices, (list, tuple)) else []
    except TypeError:
        return ""
    try:
        return " ".join(
            f"<button name='answer' value='{html.escape(c)}'>"
            f"{html.escape(c)}</button>"
            for c in items)
    except Exception:  # noqa: BLE001 -- hostile payload renders nothing
        return ""


def picker_html(choices, cid) -> str:
    """Directory-grouped radio picker; "" when unusable (fallback)."""
    try:
        groups = group_by_dir(choices)
        total = sum(len(fs) for _, fs in groups)
        if not groups or total <= THRESHOLD:
            return ""
        _ = cid  # call-site shape only; radios are label-wrapped
        parts = ["<fieldset class='treepick' id='treepick'>"
                 "<legend>Pick the file</legend>"]
        for i, (d, files) in enumerate(groups):
            label = "top level" if not d else d
            open_attr = " open" if i == 0 else ""
            parts.append(
                f"<details{open_attr}><summary>"
                f"{html.escape(label)} ({len(files)})</summary>")
            for f in files:
                base = f.rsplit("/", 1)[-1]
                parts.append(
                    f"<label><input type='radio' name='answer' "
                    f"value='{html.escape(f, quote=True)}' required> "
                    f"{html.escape(base)}</label><br>")
            parts.append("</details>")
        parts.append("<button>Check file</button></fieldset>")
        return "".join(parts)
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def branch_html(card, payload, cid) -> str:
    """Full etype-4 body: tree picker when many files, else legacy."""
    try:
        from . import cards as cardsmod  # lazy: cards.py calls this branch
        conf = cardsmod._confidence()
    except Exception:  # noqa: BLE001 -- confidence must never raise
        conf = ""
    try:
        p = payload if isinstance(payload, dict) else {}
        raw = p.get("choices", [])
        if should_pick(raw):
            g = picker_html(raw, cid)
            if g:
                return f"{g} {conf}"
        items = raw if isinstance(raw, list) else []
        return f"{legacy_html(items)} {conf}"
    except Exception:  # noqa: BLE001 -- branch must never raise
        try:
            return f"{legacy_html([])} {conf}"
        except Exception:  # noqa: BLE001 -- legacy must never raise
            return ""


def tour_entry() -> dict:
    """Tour registry entry for the where-live tree picker."""
    return {"id": "where-live-tree-picker", "kind": "improvement",
            "title": "Where-live tree picker",
            "blurb": ("Where-live cards with many files answer from a "
                      "directory-grouped tree picker instead of a wall "
                      "of buttons."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection with a live-computed sample."""
    try:
        sample = [f"groundwork/{n}.py" for n in
                  ("cards", "web", "sched", "coach")]
        sample += ["tests/test_treepick.py", "docs/tour.md",
                   "groundwork/filemap.py"]
        n_dirs = len(group_by_dir(sample))
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Where-live tree picker "
            "<small>(improvement)</small></h3>"
            "<p>Where-live cards with more than six files answer from a "
            "directory-grouped tree picker -- one section per directory, "
            "one radio per file -- instead of a wall of buttons. The "
            "picker posts the same <code>answer</code> field, so grading "
            "and disclosures do not change; short lists keep the legacy "
            "buttons byte-identical. "
            "<code>groundwork/treepick.py</code>.</p>"
            f"<p><small>Sample: {len(sample)} files group into "
            f"{n_dirs} directories.</small></p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Where-live tree picker</h3>"
                "<p>Help unavailable.</p>")
