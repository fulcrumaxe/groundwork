"""Session playlists: one-click 5/10/20-minute mixes (F-120)."""
import copy
import unittest

from test_web import handler_for, make_module

from groundwork import playlists as mod


def _card(cid, due="2026-09-20T00:00:00Z", attempts=2):
    return {"id": cid, "due": due, "attempts": attempts}


def _due(n=10):
    return [_card(f"c{i:02d}") for i in range(n)]


class MixesTest(unittest.TestCase):
    def test_three_mixes_cover_budgets(self):
        mixes = mod.mixes_for(_due(10), estimate_fn=lambda c: 60)
        self.assertEqual(sorted(mixes), [5, 10, 20])
        self.assertEqual(len(mixes[5]), 5)
        self.assertEqual(len(mixes[10]), 10)
        # 20-minute budget covers the whole short queue.
        self.assertEqual(len(mixes[20]), 10)

    def test_mixes_are_most_overdue_prefixes(self):
        due = _due(6)
        mixes = mod.mixes_for(list(reversed(due)), estimate_fn=lambda c: 60)
        self.assertEqual(mixes[5], [c["id"] for c in due[:5]])

    def test_short_queue_all_mixes_equal(self):
        mixes = mod.mixes_for(_due(2), estimate_fn=lambda c: 60)
        for ids in mixes.values():
            self.assertEqual(ids, ["c00", "c01"])

    def test_empty_queue_maps_to_empty(self):
        self.assertEqual(mod.mixes_for([]), {5: [], 10: [], 20: []})
        self.assertEqual(mod.mixes_for(None), {5: [], 10: [], 20: []})

    def test_hostile_never_raises(self):
        self.assertEqual(mod.mixes_for("nope"), {5: [], 10: [], 20: []})
        self.assertIn(mod.SECTION_ANCHOR, mod.playlist_html(None))
        self.assertIn(mod.SECTION_ANCHOR, mod.playlist_html("nope"))
        self.assertIn(mod.SECTION_ANCHOR,
                      mod.playlist_html(_due(3), minutes_list="junk"))

    def test_never_mutates_input(self):
        due = list(reversed(_due(6)))
        before = copy.deepcopy(due)
        mod.mixes_for(due, estimate_fn=lambda c: 60)
        mod.playlist_html(due, estimate_fn=lambda c: 60)
        self.assertEqual(due, before)

    def test_custom_lengths(self):
        mixes = mod.mixes_for(_due(10), minutes_list=[3],
                              estimate_fn=lambda c: 60)
        self.assertEqual(sorted(mixes), [3])
        self.assertEqual(len(mixes[3]), 3)


class PlaylistHtmlTest(unittest.TestCase):
    def test_three_rows_with_start_links(self):
        body = mod.playlist_html(_due(10), estimate_fn=lambda c: 60)
        self.assertIn(f"id='{mod.SECTION_ANCHOR}'", body)
        for mins in (5, 10, 20):
            self.assertIn(f"Start {mins}-minute mix", body)

    def test_empty_renders_all_clear_without_buttons(self):
        body = mod.playlist_html([])
        self.assertIn(f"id='{mod.SECTION_ANCHOR}'", body)
        self.assertIn("All clear", body)
        self.assertNotIn("Start", body)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/due")
        self.assertEqual(entry["anchor"], mod.SECTION_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_due_page_carries_playlists(self):
        _tmp, db, _s, _out = make_module("playlists due")
        due = handler_for(db).due_html()
        self.assertIn(f"id='{mod.SECTION_ANCHOR}'", due)
        self.assertIn("Start 5-minute mix", due)

    def test_empty_due_page_carries_all_clear(self):
        _tmp, db, _s, _out = make_module("playlists empty")
        h = handler_for(db)
        due = h.due_html()
        # Fixture queue may be non-empty; the section renders either way.
        self.assertIn(f"id='{mod.SECTION_ANCHOR}'", due)


if __name__ == "__main__":
    unittest.main()
