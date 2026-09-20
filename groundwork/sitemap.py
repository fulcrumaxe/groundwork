"""Crawler maps for self-hosters: sitemap.xml and robots.txt (I-32).

Pure renderers over a database path — the web Handler delegates here.
"""
from __future__ import annotations

import html

from . import db as dbmod

ROUTES = ["", "due", "modules", "reviews", "debt", "diagnose",
          "tour", "status"]


def sitemap_xml(db_path: str, base_url: str) -> str:
    """Machine-readable route map: every page plus every module."""
    con = dbmod.connect(db_path)
    try:
        mids = [r[0] for r in con.execute(
            "SELECT id FROM modules ORDER BY created_at DESC").fetchall()]
    finally:
        con.close()
    items = "".join(
        f"<url><loc>{html.escape(base_url)}/{u}</loc></url>" if u
        else f"<url><loc>{html.escape(base_url)}/</loc></url>"
        for u in ROUTES)
    items += "".join(
        f"<url><loc>{html.escape(base_url)}/modules/"
        f"{html.escape(m)}</loc></url>" for m in mids)
    return ("<?xml version='1.0' encoding='UTF-8'?>"
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
            + items + "</urlset>")


def robots_txt(base_url: str) -> str:
    return (f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n")
