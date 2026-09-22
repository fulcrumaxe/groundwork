"""Before/after diff view per lesson (I-107)."""
import json
import unittest

from groundwork import beforafter as bamod
from groundwork import db as dbmod

from test_web import handler_for, make_module


class PairTest(unittest.TestCase):
    def test_absent_pair_is_none_none(self):
        self.assertEqual(bamod.pair({}), (None, None))
        self.assertEqual(bamod.pair("nope"), (None, None))
        self.assertEqual(bamod.pair(None), (None, None))

    def test_after_falls_back_to_source(self):
        before, after = bamod.pair({"before": "x = 1\n", "source": "x = 2\n"})
        self.assertEqual((before, after), ("x = 1\n", "x = 2\n"))

    def test_stats_count_whole_pair(self):
        self.assertEqual(bamod.diff_stats("a\nb\n", "a\nc\nd\n"),
                         {"added": 2, "removed": 1})

    def test_diff_capped(self):
        big = "\n".join(f"l{i}" for i in range(200))
        out = bamod.unified_diff("", big)
        self.assertLessEqual(len(out.splitlines()), bamod.MAX_DIFF_LINES + 3)


class BlockTest(unittest.TestCase):
    def test_empty_state_is_empty_string(self):
        self.assertEqual(bamod.lesson_block({}), "")
        self.assertEqual(bamod.lesson_block({"summary": "hi"}), "")

    def test_block_counts_and_escapes(self):
        out = bamod.lesson_block(
            {"before": "x = 1\n", "after": "x = 2\n<script>\n"}, anchor=True)
        self.assertIn("id='beforafter'", out)
        self.assertIn("2 added", out)
        self.assertIn("1 removed", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertNotIn("<script>", out)

    def test_no_anchor_without_flag(self):
        out = bamod.lesson_block({"before": "a", "after": "b"})
        self.assertNotIn("id='beforafter'", out)
        self.assertIn("Show what changed", out)

    def test_never_raises(self):
        bamod.lesson_block(None)
        bamod.pair(42)
        bamod.diff_stats(None, None)
        bamod.unified_diff(None, None, cap="junk")

    def test_status_anchor_and_tour(self):
        self.assertIn(bamod.STATUS_ANCHOR, bamod.section_html())
        entry = bamod.tour_entry()
        self.assertEqual(
            set(entry), {"id", "kind", "title", "blurb", "path", "anchor"})


class CallerPathTest(unittest.TestCase):
    def test_legacy_page_has_no_beforafter(self):
        _tmp, db, _server, out = make_module("legacy pairless mod")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("beforafter", body)

    def test_pair_renders_through_module_page(self):
        _tmp, db, _server, out = make_module("pair change mod")
        mid = out["module_id"]
        con = dbmod.connect(db)
        try:
            row = con.execute("SELECT lessons FROM modules WHERE id=?",
                              (mid,)).fetchone()
            lessons = json.loads(row["lessons"])
            lessons[0]["before"] = "total = a - b\n"
            lessons[0]["after"] = "total = a + b\n"
            con.execute("UPDATE modules SET lessons=? WHERE id=?",
                        (json.dumps(lessons), mid))
            con.commit()
        finally:
            con.close()
        body = handler_for(db).module_html(mid)
        self.assertIn("id='beforafter'", body)
        self.assertIn("1 added", body)
        self.assertIn("1 removed", body)


if __name__ == "__main__":
    unittest.main()
