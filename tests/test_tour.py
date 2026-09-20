"""Tour tests: every registry entry points at visible UI that exists."""
import unittest

from groundwork import tour as tourmod
from groundwork import web as webmod

from test_web import handler_for, make_module


def render_path(h, path, mid):
    """Full page render, as the browser receives it (chrome + body)."""
    if path == "/":
        body = h.projects_html()
    elif path == "/due":
        body = h.due_html()
    elif path == "/modules":
        body = h.modules_html()
    elif path == "/reviews":
        body = h.history_html()
    elif path == "/debt":
        body = h.debt_html()
    elif path == "/diagnose":
        body = h.diagnose_html()
    elif path == "/status":
        body = h.status_html()
    elif mid and path == f"/modules/{mid}":
        body = h.module_html(mid)
    else:
        raise AssertionError(f"tour target has no renderer: {path}")
    return webmod.page("T", body).decode()


class RegistryShapeTest(unittest.TestCase):
    def test_batches_landed_improvements_and_features(self):
        kinds = [e["kind"] for e in tourmod.ENTRIES]
        # Batch 1: 10 improvements + 12 features; Batch 2: +5 and +6;
        # Batch 3: +5 and +5 (plus this guardrail feature itself).
        self.assertEqual(kinds.count("improvement"), 15)
        self.assertEqual(kinds.count("feature"), 19)
        self.assertEqual(len(set(kinds)), 3)  # + mvp baseline

    def test_ids_unique_and_complete(self):
        self.assertEqual(len(tourmod.BY_ID), len(tourmod.ENTRIES))
        self.assertEqual(tourmod.ORDER, [e["id"] for e in tourmod.ENTRIES])
        for e in tourmod.ENTRIES:
            self.assertTrue(e["title"] and e["blurb"])
            self.assertTrue(e["path"].startswith("/"))
            self.assertTrue(e["anchor"])

    def test_guided_chain_covers_all_entries_once(self):
        seen = []
        eid = tourmod.ORDER[0]
        ctx = tourmod.context(eid)
        self.assertEqual(ctx["prev_url"], "/tour")
        seen.append(eid)
        while ctx["next_url"] != "/tour":
            nxt = ctx["next_url"].split("tour=")[1]
            self.assertNotIn(nxt, seen)
            seen.append(nxt)
            ctx = tourmod.context(nxt)
        self.assertEqual(seen, tourmod.ORDER)

    def test_placeholders_need_module_context(self):
        e = tourmod.BY_ID["bloom-ladder"]
        self.assertEqual(tourmod.resolve(e), "/modules")
        url = tourmod.resolve(e, "m1", "lesson-add")
        self.assertEqual(url, "/modules/m1#ladder")


class TourTargetsTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("tour mod")
        self.h = handler_for(self.db)
        card = self.server.tool_list_due_reviews({"limit": 1})["due"][0]
        self.server.submit_review(card["id"], "5", 4)
        self.mid, self.lesson = self.h._tour_targets()
        self.assertTrue(self.mid and self.lesson)

    def test_every_entry_lands_on_rendered_anchor(self):
        for e in tourmod.ENTRIES:
            with self.subTest(entry=e["id"]):
                url = tourmod.resolve(e, self.mid, self.lesson)
                path, _, anchor = url.partition("#")
                body = render_path(self.h, path, self.mid)
                self.assertIn(f"id='{anchor}'", body)

    def test_guided_banner_has_prev_next_exit(self):
        ctx = tourmod.context("due-why", self.mid, self.lesson)
        raw = webmod.page("Due", self.h.due_html(), tour=ctx).decode()
        self.assertIn("tour-banner", raw)
        self.assertIn(ctx["prev_url"], raw)
        self.assertIn(ctx["next_url"], raw)
        self.assertIn("Exit tour", raw)

    def test_tour_page_lists_every_entry_with_show_me(self):
        body = self.h.tour_html()
        for e in tourmod.ENTRIES:
            with self.subTest(entry=e["id"]):
                self.assertIn(e["title"], body)
                self.assertIn(
                    tourmod.step_url(e["id"], self.mid, self.lesson), body)

    def test_status_page_has_all_sections(self):
        body = self.h.status_html()
        for sec in ("status-ci", "status-hooks", "status-cli",
                    "status-mcp", "status-exports", "status-share",
                    "status-seed", "status-sitemap", "status-csv",
                    "status-api", "status-modular"):
            self.assertIn(f"id='{sec}'", body)
        self.assertIn("/export/anki.tsv", body)
        self.assertIn("/feed.xml", body)


if __name__ == "__main__":
    unittest.main()
