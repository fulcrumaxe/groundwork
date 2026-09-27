"""Sandbox errors in plain language (I-184).

Execution-graded cards fail today with a raw ``Output: ...`` line
carrying the sandbox's stdout and truncated stderr -- a bare
traceback for a learner who may never have read one. This module
translates the stderr's exception name into one plain-language
sentence plus one fix direction.

``hint_text`` returns "" for every unknown name, so the caller keeps
its legacy feedback byte-identical on those paths: unknown errors
pass through untranslated, never mislabeled. Timeout tailoring is
out of scope (owned by I-183). Stdlib only (``html``, ``re``);
never raises.
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b27-errplain"

#: Exception name -> (plain-language meaning, one fix direction).
KNOWN = {
    "SyntaxError": (
        "Your code could not be read -- something in the spelling "
        "or punctuation is off.",
        "Look at the flagged line, then check brackets, quotes, "
        "and colons on the lines just above it."),
    "IndentationError": (
        "One line sits at a different indent than its neighbors, "
        "so its block is unclear.",
        "Line the block up with matching spaces, and never mix "
        "tabs and spaces."),
    "NameError": (
        "Your code uses a name that was never defined.",
        "Check the spelling, and make sure the variable or "
        "function is created before this line runs."),
    "UnboundLocalError": (
        "A function reads one of its own variables before giving "
        "it a value.",
        "Assign the variable earlier in the function, or pass it "
        "in as a parameter."),
    "TypeError": (
        "An operation received a value of the wrong kind.",
        "Print the types of the values involved, then convert one "
        "or pick the matching operation."),
    "ValueError": (
        "A value has the right kind but an unusable content.",
        "Print the actual value at that line, then handle or "
        "reject the bad case."),
    "IndexError": (
        "You asked a list for a position past its end.",
        "Check the list's length first, or loop over the list "
        "itself instead of counting positions."),
    "KeyError": (
        "You asked a dictionary for a key it does not hold.",
        "Check the key's spelling, or use .get() with a default "
        "when the key may be absent."),
    "AttributeError": (
        "You used a method or attribute the object does not have.",
        "Print the object's type and double-check the exact "
        "attribute name."),
    "ZeroDivisionError": (
        "Your code divides by zero.",
        "Guard the division: skip it or substitute a fallback "
        "when the divisor is zero."),
    "ModuleNotFoundError": (
        "The module you tried to import cannot be found.",
        "Check the module name's spelling."),
    "ImportError": (
        "Something in the import failed.",
        "Check that the imported name actually exists in that "
        "module."),
    "RecursionError": (
        "A function called itself too many times without stopping.",
        "Make sure every path reaches a base case that returns."),
    "AssertionError": (
        "A check inside the tests failed.",
        "Read which check the tests flag, then compare what your "
        "code returns against what the test expects."),
    "FileNotFoundError": (
        "Your code opened a file that is not there -- the sandbox "
        "runs with an empty folder.",
        "Check the file name, and do not rely on files outside "
        "your submission."),
    "RuntimeError": (
        "Your code hit a general failure while running.",
        "Read the message after the colon -- it names the specific "
        "problem."),
}

_NAME_RE = re.compile(
    r"([A-Za-z_][A-Za-z0-9_]*Error|[A-Za-z_][A-Za-z0-9_]*Exception)\b")


def _text(value) -> str:
    """Stderr as text; "" for missing/hostile input."""
    try:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", "replace")
        if isinstance(value, str):
            return value
        return ""
    except Exception:  # noqa: BLE001 -- coercion never raises
        return ""


def last_error_line(stderr) -> str:
    """Last non-empty stderr line (the exception line of a traceback).

    "" when stderr is empty or hostile. Never raises.
    """
    try:
        lines = [ln.strip() for ln in _text(stderr).splitlines()]
        lines = [ln for ln in lines if ln]
        return lines[-1] if lines else ""
    except Exception:  # noqa: BLE001
        return ""


def error_name(stderr) -> str:
    """Known exception name from the last stderr line, else "".

    Only names in KNOWN are returned, so the caller can never
    mislabel an unfamiliar failure. Never raises.
    """
    try:
        found = _NAME_RE.search(last_error_line(stderr))
        name = found.group(1) if found else ""
        return name if name in KNOWN else ""
    except Exception:  # noqa: BLE001
        return ""


def explain(stderr):
    """{"name", "plain", "fix"} for a known error; None otherwise.

    None (unknown, empty, or hostile input) means the caller renders
    its legacy feedback untouched. Never raises.
    """
    try:
        name = error_name(stderr)
        if not name:
            return None
        plain, fix = KNOWN[name]
        return {"name": name, "plain": plain, "fix": fix}
    except Exception:  # noqa: BLE001
        return None


def hint_text(stderr) -> str:
    """One plain-language feedback line; "" when untranslatable.

    "" keeps the caller's legacy ``Output: ...`` line byte-identical.
    The hint carries only fixed table strings plus the matched name,
    never raw traceback text. Never raises.
    """
    try:
        found = explain(stderr)
        if not found:
            return ""
        return (f"{found['name']} in plain words: {found['plain']} "
                f"Fix direction: {found['fix']}")
    except Exception:  # noqa: BLE001 -- feedback never raises
        return ""


def hint_html(stderr) -> str:
    """Escaped one-line hint paragraph; "" when untranslatable."""
    try:
        text = hint_text(stderr)
        if not text:
            return ""
        return f"<p class='errplain'>{html.escape(text)}</p>"
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


_SAMPLE = ('Traceback (most recent call last):\n'
           '  File "<string>", line 1, in <module>\n'
           "NameError: name 'total' is not defined\n")


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch27.py."""
    try:
        sample = hint_html(_SAMPLE)
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Sandbox errors in plain language "
            "<small>(improvement)</small></h3>"
            "<p>When written code fails the hidden tests, the grade path "
            "(<code>exercises.grade</code>, types 12/19/23) keeps its "
            "legacy <code>Output: ...</code> line and appends one "
            "plain-language sentence plus one fix direction for known "
            "errors. <code>groundwork/errplain.py</code> returns nothing "
            "for unknown names, so unfamiliar failures render exactly "
            "as today -- never mislabeled. A live sample renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Sandbox errors in plain language</h3>"
                "<p>Plain-language error help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "sandbox-errors-plain",
        "kind": "improvement",
        "title": "Sandbox errors in plain language",
        "blurb": "Failed run? One plain sentence says what the error means and where to look.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
