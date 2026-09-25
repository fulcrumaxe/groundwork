"""Library identity avatar (F-116)."""
import unittest

from groundwork import avatar as mod

from test_web import make_module


class IdentityTest(unittest.TestCase):
    def test_stable_per_key(self):
        self.assertEqual(mod.identity_for("a"), mod.identity_for("a"))
        self.assertIn(mod.identity_for("a")["shape"], mod.SHAPES)

    def test_distinct_keys_differ(self):
        seen = {mod.identity_for(f"lib-{i}")["hue_a"] for i in range(20)}
        self.assertGreater(len(seen), 1)

    def test_svg_duo_tone(self):
        svg = mod.avatar_svg("mylib")
        self.assertIn("<svg", svg)
        self.assertIn("hsl(", svg)
        self.assertNotIn("emoji", svg)

    def test_hostile_never_raises(self):
        self.assertIn("<svg", mod.avatar_svg(None))
        self.assertIn("library-identity", mod.box_html(None))

    def test_key_content_addressed(self):
        _t1, db1, _s1, _o1 = make_module("same content")
        _t2, db2, _s2, _o2 = make_module("same content")
        self.assertEqual(mod.library_key(db1), mod.library_key(db2))
        self.assertEqual(mod.library_key("/nonexistent.db"), "learner")

    def test_css_has_no_style_tags(self):
        self.assertNotIn("<style", mod.avatar_css())

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/reviews")


class CallerEffectTest(unittest.TestCase):
    def test_history_carries_identity(self):
        from groundwork import history as histmod
        _tmp, db, _s, _out = make_module("avatar history")
        body = histmod.history_html(db)
        self.assertIn("id='library-identity'", body)

    def test_mark_stable_across_renders(self):
        from groundwork import history as histmod
        _tmp, db, _s, _out = make_module("avatar stable")
        first = histmod.history_html(db)
        second = histmod.history_html(db)
        self.assertEqual(
            first.split("id='library-identity'")[1][:200],
            second.split("id='library-identity'")[1][:200])


if __name__ == "__main__":
    unittest.main()
