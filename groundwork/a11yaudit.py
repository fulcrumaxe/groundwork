"""Accessibility audit of rendered output (type 52, F-29, bloom: analyse).

The learner lists a snippet's accessibility violations; grading is a
pure checklist match against CLOSED RULES (one finding per rule, RULES
order, deterministic), so no sandbox runner is needed. Guards (never
flag): alt="" (decorative), aria-label/ledby or wrapped/for labels,
any role on clickable divs, any lang, named links, no-<html> / no-heading
fragments. Out of scope: low-contrast pairs (need computed CSS).
Parsing uses html.parser (never regex-only): escaped entities never
parse as tags, so hostile injections pass through unflagged.

generate() returns None when the snippet has no auditable surface, is
violation-free, or parsing fails -- the GENERATORS splice must treat
None as skip. Nothing here ever raises.

Pure functions, stdlib only (html/html.parser), no groundwork imports:
import-safe standalone. Registration lives in groundwork/exercises.py
(TYPES, GENERATORS, BLOOM_TYPES plus thin grade/render branches); the
pipeline analyse list gains 52 with no harness/mutation guard.
"""
from __future__ import annotations

import html
from html.parser import HTMLParser

TYPE_NUM = 52
TYPE_NAME = "a11y-audit"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b9-a11yaudit"

RULES = (
    "img-missing-alt",
    "input-missing-label",
    "div-with-onclick-no-role",
    "html-missing-lang",
    "empty-link-text",
    "h1-skip",
)

_RULE_WHY = {
    "img-missing-alt": "images need alt text (or alt=\"\" when decorative)",
    "input-missing-label": "form fields need a label or aria-label",
    "div-with-onclick-no-role": "clickable divs need a role (or a real button)",
    "html-missing-lang": "the page needs <html lang>",
    "empty-link-text": "links need an accessible name",
    "h1-skip": "headings should start at h1, not skip to h2+",
}

_MAX_ITEMS = 6  # == len(RULES): at most one finding per rule

# Tolerant aliases: rule id -> accepted plain-word spellings
# (lowercase, "_" -> "-", collapsed whitespace).
_ALIASES = {
    "img-missing-alt": {"img-missing-alt", "img alt", "missing alt",
                        "missing alt text", "alt", "alt text", "image alt", "no alt"},
    "input-missing-label": {"input-missing-label", "label", "missing label",
                            "form label", "unlabeled input", "no label"},
    "div-with-onclick-no-role": {"div-with-onclick-no-role", "div button", "div-button",
                                 "clickable div", "onclick", "onclick div",
                                 "fake button", "no role"},
    "html-missing-lang": {"html-missing-lang", "lang", "missing lang", "html lang", "no lang"},
    "empty-link-text": {"empty-link-text", "empty link", "link text", "blank link", "no link text"},
    "h1-skip": {"h1-skip", "h1", "heading", "heading order", "skipped heading", "missing h1"},
}


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _element_repr(tag: str, attrs) -> str:
    parts = [k if v is None else f'{k}="{v[:24]}"' for k, v in attrs]
    return ("<" + tag + (" " + " ".join(parts) if parts else "") + ">")[:60]


class _AuditParser(HTMLParser):
    """Single-pass collector; findings evaluated after parsing so that
    <label for> may come before or after its <input>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.surface = False
        self.findings: dict[str, dict] = {}
        self._label_fors: set[str] = set()
        self._label_depth = 0
        self._inputs: list[dict] = []
        self._saw_html = False
        self._saw_h1 = False
        self._link_stack: list[dict] = []

    def _note(self, rule: str, element: str, line: int) -> None:
        if rule not in self.findings:
            self.findings[rule] = {"rule": rule, "element": element,
                                   "line": line, "why": _RULE_WHY[rule]}

    def handle_starttag(self, tag: str, attrs: list) -> None:
        ad = {k: (v if v is not None else "") for k, v in attrs}
        line = self.getpos()[0]
        el = _element_repr(tag, attrs)
        if tag in ("img", "input", "a", "div", "html",
                   "h1", "h2", "h3", "h4", "h5", "h6"):
            self.surface = True
        if tag == "img":
            if "alt" not in ad:  # alt="" is valid decorative: no flag
                self._note("img-missing-alt", el, line)
            for frame in self._link_stack:
                if ad.get("alt", "").strip():
                    frame["named"] = True
        elif tag == "input":
            if ad.get("type", "").lower() != "hidden":
                self._inputs.append(
                    {"id": ad.get("id", ""),
                     "aria": bool(ad.get("aria-label", "").strip()
                                  or ad.get("aria-labelledby", "").strip()),
                     "wrapped": self._label_depth > 0,
                     "element": el, "line": line})
        elif tag == "label":
            self._label_depth += 1
            if ad.get("for", "").strip():
                self._label_fors.add(ad["for"].strip())
        elif tag == "div":
            if "onclick" in ad and "role" not in ad:
                self._note("div-with-onclick-no-role", el, line)
        elif tag == "html":
            self._saw_html = True
            if "lang" not in ad:  # no <html> at all: not applicable
                self._note("html-missing-lang", el, line)
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if tag == "h1":
                self._saw_h1 = True
            elif not self._saw_h1:  # no headings at all: not applicable
                self._note("h1-skip", el, line)
        if tag == "a":
            self._link_stack.append(
                {"named": bool(ad.get("aria-label", "").strip()),
                 "href": "href" in ad, "element": el, "line": line,
                 "text": []})

    def handle_endtag(self, tag: str) -> None:
        if tag == "label":
            self._label_depth = max(0, self._label_depth - 1)
        if tag == "a" and self._link_stack:
            frame = self._link_stack.pop()
            name = "".join(frame["text"]).strip()
            if frame["href"] and not name and not frame["named"]:
                self._note("empty-link-text", frame["element"],
                           frame["line"])

    def handle_data(self, data: str) -> None:
        if self._link_stack:
            self._link_stack[-1]["text"].append(data)

    def close(self) -> None:
        super().close()
        for inp in self._inputs:
            if inp["aria"]:  # aria-label/ledby satisfies labeling
                continue
            if inp["id"] and inp["id"] in self._label_fors:
                continue
            if inp["wrapped"]:
                continue
            self._note("input-missing-label", inp["element"], inp["line"])


def audit(snippet) -> list[dict]:
    """All findings for one snippet, in RULES order. Never raises."""
    try:
        if isinstance(snippet, list):
            text = "\n".join(str(l) for l in snippet)
        else:
            text = str(snippet or "")
        if not text.strip():
            return []
        parser = _AuditParser()
        parser.feed(text)
        parser.close()
        if not parser.surface:
            return []
        return [parser.findings[r] for r in RULES if r in parser.findings][
            :_MAX_ITEMS]
    except Exception:  # noqa: BLE001 -- audit must never raise
        return []


def generate(ex_id, concept, snippet, ctx):
    """Build the type-52 exercise dict, or None when there is nothing
    auditable (no surface, violation-free, or unparsable)."""
    try:
        ctx = ctx or {}
        findings = audit(snippet if isinstance(snippet, list)
                         else [str(snippet or "")] if snippet else [])
        if not findings:
            return None
        name = _concept_field(concept, "name", "page") or "page"
        node = _concept_field(concept, "node_id", name)
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        shown = "\n".join(
            f"{i}: {f['element']} (line {f['line']})" for i, f in enumerate(findings))
        rules = ", ".join(RULES)
        body = snippet if isinstance(snippet, list) else [str(snippet or "")]
        body = "\n".join(body)
        front = ("Read this rendered HTML and list every accessibility "
                 "violation, one per line as `id=rule` "
                 "(plain words count too, e.g. `0=missing alt text`).\n"
                 f"Rule ids: {rules}.\n```html\n"
                 f"{body[:900]}\n```\n"
                 f"Marked elements:\n{shown}")
        back = "\n".join(f"{i}={f['rule']}" for i, f in enumerate(findings))
        first = findings[0]
        first_line = (snippet or [""])[0] if isinstance(snippet, list) \
            else str(snippet or "")
        hints = [
            "Check images, form fields, clickable divs, links, page "
            "language, and heading order -- one rule per item.",
            (f"Look at {file}:{line}: `{first_line.strip()}`"
             if (snippet and file) else "Re-read the snippet."),
            f"Worked step: item 0 ({first['element']}) is "
            f"`{first['rule']}` ({first['why']}). Now name the rest.",
        ]
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": node, "concept": name,
            "file": file, "line": line, "commit": commit,
            "hints": hints, "front": front, "back": back,
            "payload": {"checklist": [
                {"id": i, "rule": f["rule"], "element": f["element"],
                 "line": f["line"], "why": f["why"]}
                for i, f in enumerate(findings)],
                "rules": list(RULES), "grounded": True},
        }
    except Exception:  # noqa: BLE001 -- generate must never raise
        return None


def _norm_claim(raw: str) -> str | None:
    word = " ".join(str(raw).strip().lower().replace("_", "-").split())
    if not word:
        return None
    for rule in RULES:
        if word == rule or word in _ALIASES[rule]:
            return rule
    return None


def _parse_claims(submission: str) -> tuple[set[str], list[str]]:
    """Return (claimed rule ids, unknown non-empty chunks)."""
    claimed: set[str] = set()
    unknown: list[str] = []
    text = str(submission).replace(",", "\n").replace(";", "\n")
    for chunk in text.splitlines():
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" in chunk:
            _, chunk = chunk.split("=", 1)
        rule = _norm_claim(chunk)
        if rule is None:
            unknown.append(chunk.strip()[:40])
        else:
            claimed.add(rule)
    return claimed, unknown


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Checklist match: every required rule named passes, with partial
    credit. Empty/hostile submissions fail closed. Never raises."""
    _ = runner
    try:
        items = ((exercise or {}).get("payload", {}) or {}).get(
            "checklist", [])
        if not items:
            return _fail("No checklist to grade.")
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("List each violation (`id=rule`, one per line; "
                         "plain words count too).")
        if len(items) == 1 and "=" not in text:
            claimed = {_norm_claim(text)} - {None}
            unknown: list[str] = [] if claimed else [text.strip()[:40]]
        else:
            claimed, unknown = _parse_claims(text)
        required = [it["rule"] for it in items]
        missing = [r for r in required if r not in claimed]
        score = (len(required) - len(missing)) / len(required)
        if not missing:
            return {"pass": True, "score": 1.0,
                    "feedback": f"All {len(required)} violations named."}
        detail = (f"Found {len(required) - len(missing)}/{len(required)}: "
                  f"missing {', '.join(missing)}.")
        if unknown:
            detail += f" Unrecognized: {', '.join(sorted(set(unknown)))}."
        return {"pass": False, "score": score, "feedback": detail}
    except Exception:  # noqa: BLE001 -- grading must never raise
        return _fail("Grader could not read the submission -- list one "
                     "violation per line.")


def render(exercise: dict) -> str:
    """Article HTML: marked elements, audit textarea, hints, file footer."""
    p = (exercise or {}).get("payload", {}) or {}
    items = p.get("checklist", [])
    front = html.escape(str((exercise or {}).get("front", "")))
    rows = "".join(
        f"<li>item {it['id']}: <code>{html.escape(str(it.get('element', '')))}</code> "
        f"<small>(line {it.get('line', '?')})</small></li>"
        for it in items)
    return (
        f"<article><h3>{html.escape(str((exercise or {}).get('concept', '')))} "
        f"· {html.escape(str((exercise or {}).get('type_name', TYPE_NAME)))}</h3>"
        f"<p>{front}</p>"
        f"<p><small>Rules: {', '.join(p.get('rules', list(RULES)))}. "
        f"Example answer: <code>0=img-missing-alt</code>.</small></p>"
        f"<form method='post'><textarea name='answer' rows='6' cols='40' "
        f"placeholder='0=img-missing-alt'>"
        f"</textarea><br><button>Submit audit</button></form>"
        f"<ol>{rows}</ol>"
        + "".join(f"<details><summary>Hint {i + 1}</summary>"
                  f"{html.escape(h)}</details>"
                  for i, h in enumerate((exercise or {}).get("hints", [])))
        + f"<p><small>{html.escape(str((exercise or {}).get('file', '')))}:"
        f"{(exercise or {}).get('line', 0)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Accessibility audit <small>(feature)</small></h3>"
        "<p>Read a rendered HTML snippet and list its accessibility "
        "violations — missing alt, missing label, clickable div, missing "
        "lang, empty link, skipped h1 — checklist-graded with tolerant "
        "word matching, no sandbox. "
        "<code>groundwork/a11yaudit.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "a11y-audit", "kind": "feature",
            "title": "Accessibility audit",
            "blurb": "Spot the access barriers in rendered HTML — missing alt, labels, roles, lang, link names, heading order.",
            "path": "/status", "anchor": "status-b9-a11yaudit"}
