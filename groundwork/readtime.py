"""Estimated read time per lesson (I-101).

Word-count over the lesson's study text at a planning rate of 200 wpm,
minimum one minute. Pure function of the stored lesson dict — no I/O.
"""
from __future__ import annotations

WPM = 200

_TEXT_KEYS = ("summary", "docstring", "key_lines", "source")


def _words(value) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        return len(value.split())
    if isinstance(value, (list, tuple)):
        return sum(_words(v) for v in value)
    if isinstance(value, dict):
        return sum(_words(v) for v in value.values())
    return len(str(value).split())


def minutes_for(lesson: dict) -> int:
    """Estimated minutes to read one lesson; at least 1."""
    if not isinstance(lesson, dict):
        return 1
    total = sum(_words(lesson.get(k)) for k in _TEXT_KEYS)
    total += _words(lesson.get("how")) + _words(lesson.get("worked"))
    return max(1, round(total / WPM))
