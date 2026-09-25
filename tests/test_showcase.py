"""Private badge showcase gallery (F-114)."""
import unittest

from groundwork import showcase as mod

from test_web import make_module


class GalleryTest(unittest.TestCase):
    def test_empty_db_placeholder(self):
        _tmp, db, _s, _out = make_module("showcase empty")
        body = mod.gallery_html(db)
        self.assertIn("id='showcase'", body)
        self.assertIn("showcase-locked", body)
        self.assertIn("No badges yet", mod.gallery_html("/nonexistent.db"))

    def test_owned_tiles_sealed(self):
        from test_partytrick import _own, _cid
        _tmp, db, _s, _out = make_module("showcase owned")
        _own(db, _cid(db))
        body = mod.gallery_html(db)
        self.assertIn("showcase-tile", body)
        self.assertIn("owned-badge", body)
        self.assertIn("cbadge", body)

    def test_locked_stay_plain(self):
        _tmp, db, _s, _out = make_module("showcase locked")
        body = mod.gallery_html(db)
        self.assertNotIn("cbadge", body)

    def test_hostile_never_raises(self):
        self.assertEqual(mod.badges("/nonexistent.db"), [])
        self.assertIn("showcase", mod.gallery_html("/nonexistent.db"))

    def test_css_has_no_style_tags(self):
        self.assertNotIn("<style", mod.showcase_css())

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/reviews")


class CallerEffectTest(unittest.TestCase):
    def test_history_carries_gallery(self):
        from groundwork import history as histmod
        _tmp, db, _s, _out = make_module("showcase history")
        body = histmod.history_html(db)
        self.assertIn("id='showcase'", body)

    def test_tile_set_changes_after_pass(self):
        from test_partytrick import _own, _cid
        from groundwork import history as histmod
        _tmp, db, _s, _out = make_module("showcase pass")
        before = histmod.history_html(db)
        self.assertNotIn("owned-badge", before)
        _own(db, _cid(db))
        after = histmod.history_html(db)
        self.assertIn("owned-badge", after)


if __name__ == "__main__":
    unittest.main()
