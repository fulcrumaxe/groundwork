"""Theme unlocks (F-115)."""
import unittest

from groundwork import themeunlock as mod

from test_web import make_module


class UnlockTest(unittest.TestCase):
    def test_base_always_unlocked(self):
        _tmp, db, _s, _out = make_module("themes base")
        states = {p["name"]: p["locked"] for p in mod.unlocked(db)}
        self.assertFalse(states["paper"])
        self.assertTrue(states["moss"])
        self.assertTrue(states["dusk"])
        self.assertTrue(states["canopy"])

    def test_first_owned_unlocks_moss(self):
        from test_partytrick import _own, _cid
        _tmp, db, _s, _out = make_module("themes moss")
        _own(db, _cid(db))
        states = {p["name"]: p["locked"] for p in mod.unlocked(db)}
        self.assertFalse(states["moss"])
        self.assertTrue(states["dusk"])

    def test_gallery_names_unlock_path(self):
        _tmp, db, _s, _out = make_module("themes gallery")
        body = mod.gallery_html(db)
        self.assertIn("theme-unlocks", body)
        self.assertIn("locked — own 1 concept", body)
        self.assertIn("data-themes", body)
        self.assertIn("localStorage", body)

    def test_hostile_never_raises(self):
        self.assertEqual(mod.progress("/nonexistent.db"),
                         {"owned": 0, "certificates": 0})
        self.assertIn("theme-unlocks",
                      mod.gallery_html("/nonexistent.db"))

    def test_css_has_no_style_tags(self):
        self.assertNotIn("<style", mod.theme_css())

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/reviews")


class CallerEffectTest(unittest.TestCase):
    def test_history_carries_gallery(self):
        from groundwork import history as histmod
        _tmp, db, _s, _out = make_module("themes history")
        body = histmod.history_html(db)
        self.assertIn("id='theme-unlocks'", body)

    def test_gallery_unlocks_with_proof(self):
        from test_partytrick import _own, _cid
        from groundwork import history as histmod
        _tmp, db, _s, _out = make_module("themes proof")
        before = histmod.history_html(db)
        self.assertIn("locked — own 1 concept", before)
        _own(db, _cid(db))
        after = histmod.history_html(db)
        self.assertNotIn("locked — own 1 concept", after)
        self.assertIn("data-theme='moss'", after)


if __name__ == "__main__":
    unittest.main()
