"""Kids mode: ?kids=1 easy words, big targets, parent dashboard (F-141)."""
import unittest

from groundwork import emoji as emojimod
from groundwork import kids as mod
from test_web import handler_for, make_module


class KidsUnitTest(unittest.TestCase):
    def test_flag_parsing(self):
        self.assertTrue(mod.is_kids({"kids": ["1"]}))
        self.assertTrue(mod.is_kids({"kids": ["0", "1"]}))
        self.assertTrue(mod.is_kids("1"))
        self.assertFalse(mod.is_kids({"kids": ["0"]}))
        self.assertFalse(mod.is_kids({"kids": ["yes"]}))
        self.assertFalse(mod.is_kids({"kids": []}))
        self.assertFalse(mod.is_kids({}))
        self.assertFalse(mod.is_kids(None))

    def test_flag_never_raises(self):
        for bad in (None, {}, {"kids": [None]}, 0, ["1"], object()):
            self.assertFalse(mod.is_kids(bad))

    def test_simplify_map(self):
        self.assertEqual(mod.simplify("No attempts yet."), "No tries yet.")
        self.assertEqual(mod.simplify("Utilize the configuration."),
                         "Use the settings.")
        self.assertEqual(mod.simplify("ACCURACY 80%"), "SCORE 80%")
        self.assertEqual(
            mod.simplify("Submitted implementations re-executed."),
            "Submitted implementations re-executed.")
        self.assertIsNone(mod.simplify(None))
        self.assertEqual(mod.simplify(5), 5)

    def test_simplify_html_skips_tags_and_code(self):
        page = ("<p id='attempts'>No attempts yet. "
                "<a href='/due?x=attempts'>Due</a></p>"
                "<pre>attempts = utilize(x)</pre>"
                "<script>var a = 'attempts';</script>")
        out = mod.simplify_html(page)
        self.assertIn("No tries yet.", out)
        self.assertIn("id='attempts'", out)
        self.assertIn("/due?x=attempts", out)
        self.assertIn("<pre>attempts = utilize(x)</pre>", out)
        self.assertIn("var a = 'attempts';", out)
        self.assertIsNone(mod.simplify_html(None))

    def test_css_ascii_and_scoped(self):
        css = mod.kids_css()
        self.assertTrue(css.isascii())
        self.assertEqual(emojimod.scan_text(css), [])
        self.assertIn(".kids", css)
        self.assertIn("min-height", css)
        self.assertNotIn("<style", css)

    def test_parent_dashboard_counts(self):
        _tmp, db, _server, _out = make_module("kids dash mod")
        dash = mod.parent_html(db)
        self.assertIn("id='parent-dash'", dash)
        self.assertIn("1 projects", dash)
        self.assertIn("tries", dash)
        self.assertIn("kids=1", dash)
        self.assertTrue(dash.isascii())
        self.assertEqual(emojimod.scan_text(dash), [])

    def test_parent_dashboard_never_raises(self):
        for bad in ("", None):
            self.assertIn("0 projects", mod.parent_html(bad))

    def test_page_wrap_fallback_identical(self):
        body = "<p>No attempts yet.</p>"
        self.assertEqual(mod.page_html(body, None, ""), body)
        self.assertEqual(mod.page_html(body, {}, ""), body)
        self.assertEqual(mod.page_html(body, {"kids": ["0"]}, ""), body)
        self.assertIsNone(mod.page_html(None, {"kids": ["1"]}, ""))


class KidsEffectTest(unittest.TestCase):
    def test_empty_history_legacy_bytes_without_flag(self):
        _tmp, db, _server, _out = make_module("kids legacy mod")
        body = handler_for(db).history_html(None)
        self.assertIn("No attempts yet.", body)
        self.assertNotIn("kids-mode", body)
        self.assertNotIn("parent-dash", body)
        self.assertNotIn("class='kids'", body)
        self.assertEqual(handler_for(db).history_html({}), body)
        self.assertEqual(handler_for(db).history_html({"kids": ["0"]}), body)

    def test_empty_history_gains_kids_mode(self):
        _tmp, db, _server, _out = make_module("kids live mod")
        body = handler_for(db).history_html({"kids": ["1"]})
        self.assertIn("id='kids-mode'", body)
        self.assertIn("class='kids'", body)
        self.assertIn("id='parent-dash'", body)
        self.assertIn("No tries yet.", body)
        self.assertNotIn("No attempts yet.", body)
        self.assertIn("id='bests'", body)
        self.assertIn("/due", body)

    def test_reviewed_history_gains_kids_mode(self):
        _tmp, db, server, _out = make_module("kids full mod")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        legacy = handler_for(db).history_html(None)
        self.assertNotIn("parent-dash", legacy)
        kids = handler_for(db).history_html({"kids": ["1"]})
        self.assertIn("id='parent-dash'", kids)
        self.assertIn("1 tries", kids)
        self.assertIn("Calibration: score", kids)
        self.assertIn("id='attempts'", kids)


class KidsShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["id"], "kids-mode")

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())
        self.assertIn("?kids=1", mod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])
        self.assertTrue(src.isascii())


if __name__ == "__main__":
    unittest.main()
