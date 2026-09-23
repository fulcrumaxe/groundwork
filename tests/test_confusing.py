"""Per-section confusing flags and the regen queue (I-134)."""
import io
import unittest
from urllib.parse import quote

from groundwork import confusing as mod
from groundwork import db as dbmod
from groundwork import lessons as lesmod
from groundwork import web as webmod

from test_web import handler_for, make_module


class NormalizeTest(unittest.TestCase):
    def test_truthy_only(self):
        self.assertEqual(mod.normalize_flags({"a": True, "b": 0, "c": ""}),
                         {"a": True})

    def test_hostile_yields_empty(self):
        for bad in (None, [], "x", 5, True):
            self.assertEqual(mod.normalize_flags(bad), {})

    def test_blank_keys_dropped(self):
        self.assertEqual(mod.normalize_flags({"  ": True}), {})


class FlagTest(unittest.TestCase):
    def test_is_confusing(self):
        self.assertTrue(mod.is_confusing("b", {"b": True}))
        self.assertFalse(mod.is_confusing("a", {"b": True}))

    def test_is_confusing_no_data_fallback(self):
        for bad in (None, {}, [], "x"):
            self.assertFalse(mod.is_confusing("b", bad))
        self.assertFalse(mod.is_confusing(None, {"b": True}))

    def test_mark_does_not_mutate(self):
        src = {"a": True}
        out = mod.mark(src, "b")
        self.assertEqual(out, {"a": True, "b": True})
        self.assertEqual(src, {"a": True})

    def test_unmark_drops_only_target(self):
        out = mod.unmark({"a": True, "b": True}, "a")
        self.assertEqual(out, {"b": True})


class SectionIdTest(unittest.TestCase):
    def test_slug_rule(self):
        self.assertEqual(mod.section_id("Hello, World!"), "hello-world")

    def test_duplicates_suffixed(self):
        self.assertEqual(mod.section_id("Words", ["words"]), "words-2")
        self.assertEqual(mod.section_id("Words", ["words", "words-2"]),
                         "words-3")

    def test_hostile_falls_back(self):
        self.assertEqual(mod.section_id(None), "section")
        self.assertEqual(mod.section_id(""), "section")


class QueueTest(unittest.TestCase):
    def test_empty_flags_empty_queue(self):
        for bad in (None, {}, {"a": False}):
            self.assertEqual(mod.regen_queue(bad), [])

    def test_insertion_order_without_page_order(self):
        self.assertEqual(mod.regen_queue({"b": True, "d": True}),
                         ["b", "d"])

    def test_page_order_wins(self):
        self.assertEqual(
            mod.regen_queue({"b": True, "d": True}, ["d", "b", "z"]),
            ["d", "b"])

    def test_unflagged_section_leaves_queue(self):
        q = mod.regen_queue(mod.unmark({"b": True, "d": True}, "b"))
        self.assertEqual(q, ["d"])

    def test_hostile_never_raises(self):
        self.assertEqual(mod.regen_queue(None, "nope"), [])
        self.assertEqual(mod.queue_count(None), 0)

    def test_queue_count(self):
        self.assertEqual(mod.queue_count({"a": True, "b": True}), 2)


class RenderTest(unittest.TestCase):
    def test_banner_empty_is_legacy_fallback(self):
        for bad in (None, {}):
            self.assertEqual(mod.queue_banner_html(bad), "")

    def test_banner_names_flagged_only(self):
        body = mod.queue_banner_html({"b": True, "d": True})
        self.assertIn("2 section(s)", body)
        self.assertIn("b", body)

    def test_button_posts_section(self):
        body = mod.flag_button_html("b", False, "m:c", "/modules/m")
        self.assertIn("confusing_section", body)
        self.assertIn("/concepts/m:c/confusing", body)
        self.assertIn("Mark confusing", body)
        on = mod.flag_button_html("b", True, "m:c", "/modules/m")
        self.assertIn("Confusing (flagged)", on)

    def test_button_hostile_empty(self):
        self.assertEqual(mod.flag_button_html(None), "")
        self.assertEqual(mod.flag_button_html("  "), "")

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "confusing-sections", "kind": "improvement",
            "title": "Flag the confusing section",
            "blurb": ("Mark the one block that lost you and it alone "
                      "joins the rewrite queue."),
            "path": "/status", "anchor": mod.STATUS_ANCHOR})


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("conf mod")
        dbmod.init_db(self.db)
        con = dbmod.connect(self.db)
        try:
            self.cid = con.execute(
                "SELECT id FROM concepts LIMIT 1").fetchone()[0]
            self.mid = con.execute(
                "SELECT module_id FROM concepts LIMIT 1").fetchone()[0]
        finally:
            con.close()
        self.key = f"{self.cid}#what-it-does"

    def test_record_roundtrip(self):
        self.assertIn("error", mod.record(self.db, "nope", "1"))
        self.assertIn("error", mod.record(self.db, self.key, "2"))
        ok = mod.record(self.db, self.key, "1")
        self.assertEqual(ok["module_id"], self.mid)
        self.assertEqual(mod.flags_for_module(self.db, self.mid),
                         {self.key: True})
        mod.record(self.db, self.key, "0")
        self.assertEqual(mod.flags_for_module(self.db, self.mid), {})

    def test_post_route_flags_end_to_end(self):
        h = handler_for(self.db)
        h.path = f"/concepts/{self.cid}/confusing"
        raw = (f"confusing_section={quote(self.key, safe='')}"
               f"&confusing=1&origin=%2Fmodules%2F{self.mid}").encode()
        h.headers = {"Content-Length": str(len(raw))}
        h.rfile = io.BytesIO(raw)
        h._send = lambda data, code=200, ctype="text/html": setattr(
            h, "_captured", (data, code, ctype))
        h.do_POST()
        data, code, _ctype = h._captured
        self.assertEqual(code, 200)
        self.assertIn("Flag saved", data.decode())
        self.assertEqual(mod.flags_for_module(self.db, self.mid),
                         {self.key: True})


class CallerEffectTest(unittest.TestCase):
    def test_lesson_blocks_carry_toggles(self):
        import json
        tmp, db, server, out = make_module("confusing render mod")
        con = dbmod.connect(db)
        try:
            row = con.execute("SELECT lessons FROM modules WHERE id=?",
                              (out["module_id"],)).fetchone()[0]
            lesson = json.loads(row or "[]")[0]
            cid = con.execute(
                "SELECT id FROM concepts WHERE module_id=? LIMIT 1",
                (out["module_id"],)).fetchone()[0]
        finally:
            con.close()
        without = lesmod.render_levels(lesson, 0.0, 0, "auto", "/modules/m")
        self.assertNotIn("confusing_section", without)
        with_flags = lesmod.render_levels(
            lesson, 0.0, 0, "auto", "/modules/m",
            confusing={}, confusing_cid=cid)
        self.assertIn("confusing_section", with_flags)
        self.assertIn(f"/concepts/{cid}/confusing", with_flags)

    def test_module_page_banner_and_legacy_fallback(self):
        tmp, db, server, out = make_module("confusing page mod")
        mid = out["module_id"]
        con = dbmod.connect(db)
        try:
            cid = con.execute(
                "SELECT id FROM concepts WHERE module_id=? LIMIT 1",
                (mid,)).fetchone()[0]
        finally:
            con.close()
        plain = handler_for(db).module_html(mid)
        # Legacy fallback: toggles render unflagged, but no banner.
        self.assertNotIn("regen-queue", plain)
        self.assertIn("Mark confusing", plain)
        mod.record(db, f"{cid}#what-it-does", "1")
        flagged = handler_for(db).module_html(mid)
        self.assertIn("regen-queue", flagged)
        self.assertIn("1 section(s)", flagged)
        self.assertIn("Confusing (flagged)", flagged)


if __name__ == "__main__":
    unittest.main()
