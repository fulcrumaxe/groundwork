"""Print stylesheet: lessons print cleanly as study sheets (I-27).

One function, no DB changes. The web layer appends its output to the
<style> block so File > Print (or print to PDF) yields a readable
study sheet: chrome hidden, content ink-friendly, page breaks sane.
"""
from __future__ import annotations


def print_css() -> str:
    """Return @media print CSS for lesson study sheets."""
    return (
        "@media print{"
        "nav,.skip,.copylink,form,button,input,textarea{display:none}"
        "body{max-width:100%;margin:0;font-family:Georgia,serif;color:#000}"
        "article{border:none;padding:0}"
        "h2{break-after:avoid}pre{break-inside:avoid}"
        "a{color:#000;text-decoration:none}"
        "}"
    )
