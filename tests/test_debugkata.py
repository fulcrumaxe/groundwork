"""Debugging kata library (F-88)."""
import unittest

from groundwork import debugkata as dkmod


class ShapesTest(unittest.TestCase):
    def test_catalog_shape(self):
        self.assertEqual(len(dkmod.list_shapes()), 8)
        self.assertEqual(len(set(dkmod.list_shapes())), 8)
        for sid in dkmod.list_shapes():
            kata = dkmod.kata_by_id(sid)
            for key in ("id", "title", "buggy", "fixed", "failing_call",
                        "blurb", "spot_rule"):
                self.assertTrue(kata[key], (sid, key))
            self.assertNotEqual(kata["buggy"], kata["fixed"])
        self.assertIsNone(dkmod.kata_by_id("nope"))
        self.assertIsNone(dkmod.kata_by_id(None))


class MatchTest(unittest.TestCase):
    def test_range_snippet_matches_fencepost(self):
        got = dkmod.katas_for("total", ["for i in range(len(xs)):", "    use(i)"])
        self.assertTrue(got)
        self.assertEqual(got[0]["id"], "fencepost-range")
        self.assertLessEqual(len(got), dkmod.MAX_KATAS)

    def test_unknown_and_empty_match_nothing(self):
        self.assertEqual(dkmod.katas_for("c", ["x = 1"]), [])
        self.assertEqual(dkmod.katas_for("c", []), [])
        self.assertEqual(dkmod.katas_for("c", None), [])
        self.assertEqual(dkmod.katas_for(None, None), [])

    def test_never_raises_on_garbage(self):
        self.assertEqual(dkmod.katas_for(42, 42), [])


class EffectTest(unittest.TestCase):
    def test_enrich_empty_snippet_leaves_lesson(self):
        lesson = {"name": "add", "summary": "x"}
        self.assertEqual(dkmod.enrich_lesson(dict(lesson), []), lesson)
        self.assertEqual(dkmod.enrich_lesson(None, []), None)

    def test_enrich_matching_snippet_adds_kata(self):
        lesson = {"name": "total",
                  "source": "for i in range(len(xs)):\n    use(i)"}
        out = dkmod.enrich_lesson(dict(lesson), lesson["source"])
        self.assertIn("kata", out)
        block = dkmod.lesson_block(out)
        self.assertIn("Failing call", block)
        self.assertIn("debugkata", block)
        self.assertEqual(dkmod.lesson_block({"name": "x"}), "")
        self.assertEqual(dkmod.lesson_block(None), "")

    def test_render_rejects_garbage(self):
        self.assertEqual(dkmod.render_kata(None), "")
        self.assertEqual(dkmod.render_kata({}), "")
        out = dkmod.render_kata(dkmod.kata_by_id("off-by-one"))
        self.assertIn("IndexError", out)
        self.assertNotIn("<script", out)


class SectionTest(unittest.TestCase):
    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{dkmod.STATUS_ANCHOR}'",
                      dkmod.section_html())
        e = dkmod.tour_entry()
        self.assertEqual(e["id"], "debugkata-library")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["anchor"], dkmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
