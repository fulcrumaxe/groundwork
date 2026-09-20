"""Leveled explanations: the same concept told four ways.

Levels: 1 Plain words, 2 Beginner, 3 Intermediate, 4 Expert. Generated at
render time from a stored lesson dict, so they work with no LLM and no
re-ingest. Auto-placement comes from concept mastery (low mastery ->
plainer words).
"""
from __future__ import annotations

GLOSSARY = {
    "function": "a reusable set of instructions you can run by name",
    "argument": "an input value you hand to a function when you run it",
    "parameter": "the named slot a function declares for an input value",
    "return": "handing an answer back to whoever ran the function",
    "variable": "a named box that holds a value which can change",
    "call": "running a function",
    "module": "one file of code",
    "test": "a check that code does what it should",
    "bug": "a mistake in code that makes it misbehave",
    "trace": "the values a variable takes, step by step, as code runs",
    "class": "a blueprint for building objects that bundle data and behaviour",
    "method": "a function that belongs to a class",
    "loop": "code that repeats",
    "condition": "a yes/no question the code branches on",
    "recursion": "a function that runs itself to solve smaller pieces",
    "exception": "an error signal the code raises when something goes wrong",
    "import": "bringing code from another file into this one",
}

PLAIN_KIND = {
    "function": "a reusable set of instructions",
    "method": "a reusable set of instructions attached to a blueprint",
    "class": "a blueprint for building things",
    "module": "a file of code",
}

LEVEL_TITLES = {1: "Plain words", 2: "Beginner", 3: "Intermediate", 4: "Expert"}


def find_terms(text: str) -> list[tuple[str, str]]:
    """Glossary terms appearing in text (word-boundary match)."""
    import re
    found = []
    for term, definition in GLOSSARY.items():
        term = term.strip()
        if not term or not definition:
            continue
        if re.search(r"\b" + re.escape(term) + r"s?\b", text.lower()):
            found.append((term, definition))
    return found[:8]


def auto_level(mastery: float, n_reviews: int) -> int:
    """Place the learner: new/weak -> plain words, strong -> technical."""
    if n_reviews == 0:
        return 2
    if mastery < 0.3:
        return 1
    if mastery < 0.6:
        return 2
    if mastery < 0.85:
        return 3
    return 4


def _narrate_worked(lesson: dict) -> str:
    w = lesson.get("worked") or {}
    if w.get("call") and w.get("output") is not None:
        s = (f"For example: running {w['call']} gives {w['output']}.")
        if w.get("trace"):
            t = w["trace"]
            seq = ", then ".join(f"{v}" for v in t["steps"][:6])
            s += f" Along the way, {t['var']} becomes: {seq}."
        return s
    return ""


def _plain_big_idea(lesson: dict) -> str:
    kind_word = PLAIN_KIND.get(lesson.get("kind", ""), "a piece of code")
    doc = (lesson.get("docstring") or "").splitlines()
    first = doc[0].strip() if doc else ""
    if first and len(first) < 160 and "`" not in first:
        return first
    return (f"{lesson['name']} is {kind_word} living in {lesson['file']}. "
            f"You use it when you need what it does, without redoing its work.")


def levels_for(lesson: dict) -> list[dict]:
    """Four expository levels; each is {n, title, blocks:[{h, b}]} (plain text)."""
    name, kind = lesson["name"], lesson.get("kind", "function")
    summary = lesson.get("summary", "")
    doc = (lesson.get("docstring") or "").strip()
    how = lesson.get("how", [])
    source = lesson.get("source") or ""
    callers = lesson.get("callers", [])
    callees = lesson.get("callees", [])
    narrated = _narrate_worked(lesson)
    terms = find_terms(f"{summary} {' '.join(how)} {doc}")

    l1 = [
        {"h": "The big idea", "b": _plain_big_idea(lesson)},
    ]
    if narrated:
        l1.append({"h": "See it happen", "b": narrated})
    if terms:
        l1.append({"h": "Words you'll see",
                    "b": "; ".join(f"{t} = {d}" for t, d in terms)})
    l1.append({"h": "Where it lives",
               "b": f"In {lesson['file']}, line {lesson.get('line', '?')}. "
                    f"Open the code box below when you're ready."})

    l2 = [{"h": "What it does", "b": summary}]
    if doc:
        l2.append({"h": "Its own description", "b": doc.splitlines()[0][:400]})
    if how:
        l2.append({"h": "How it works",
                   "b": "\n".join(f"{i + 1}. {s}" for i, s in enumerate(how))})
    if narrated:
        l2.append({"h": "Worked example", "b": narrated})
    if terms:
        l2.append({"h": "Vocabulary",
                    "b": "; ".join(f"{t}: {d}" for t, d in terms)})

    l3 = [{"h": "Summary", "b": summary}]
    if how:
        l3.append({"h": "Step by step",
                   "b": "\n".join(f"{i + 1}. {s}" for i, s in enumerate(how))})
    if narrated:
        l3.append({"h": "Measured run", "b": narrated})
    rel = []
    if callers:
        rel.append("called by " + ", ".join(callers[:5]))
    if callees:
        rel.append("depends on " + ", ".join(callees[:5]))
    if rel:
        l3.append({"h": "In the codebase", "b": "; ".join(rel) + "."})
    if source:
        l3.append({"h": "Source", "b": source[:2000], "pre": True})

    sig = source.splitlines()[0] if source else f"{name}(…)"
    locs = len(source.splitlines()) if source else 0
    l4 = [{"h": "Contract", "b": f"{sig} — {kind} @ {lesson['file']}:{lesson.get('line', '?')} "
                                 f"({locs} LOC). {summary}"}]
    edge = []
    if callers:
        edge.append("callers: " + ", ".join(callers[:8]))
    if callees:
        edge.append("deps: " + ", ".join(callees[:8]))
    if edge:
        l4.append({"h": "Blast radius", "b": "; ".join(edge) + "."})
    l4.append({"h": "Worth probing",
               "b": f"What breaks if {name} changes contract? Which caller would feel it first?"})

    return [{"n": 1, "title": "Plain words", "blocks": l1,
             "code": source[:2000]},
            {"n": 2, "title": "Beginner", "blocks": l2,
             "code": source[:2000]},
            {"n": 3, "title": "Intermediate", "blocks": l3, "code": ""},
            {"n": 4, "title": "Expert", "blocks": l4,
             "code": source.splitlines()[0] if source else ""}]
