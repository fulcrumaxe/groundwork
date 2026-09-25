"""Focus timer with queue auto-fill (F-119)."""
import unittest

from groundwork import focustimer as mod

from test_web import handler_for, make_module


def _due(n=10):
    return [{"id": f"c{i}"} for i in range(n)]


class MixTest(unittest.TestCase):
    def test_block_covers_eight(self):
        self.assertEqual(len(mod.mix_for(_due(10))), 8)
        self.assertEqual(mod.mix_for(_due(10))[0], "c0")

    def test_short_queue_covers_all(self):
        self.assertEqual(mod.mix_for(_due(3)), ["c0", "c1", "c2"])

    def test_empty_queue_free_time(self):
        self.assertEqual(mod.mix_for([]), [])
        body = mod.timer_html([])
        self.assertIn("Queue clear", body)
        self.assertIn(f"id='{mod.SECTION_ANCHOR}'", body)

    def test_hostile_never_raises(self):
        self.assertEqual(mod.mix_for(None), [])
        self.assertEqual(mod.mix_for("nope"), [])
        self.assertIn(mod.SECTION_ANCHOR, mod.timer_html(None))

    def test_timer_shape(self):
        body = mod.timer_html(_due(10))
        self.assertIn("25-minute block covers 8 cards", body)
        self.assertIn("data-focustimer", body)
        self.assertIn("25:00", body)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/due")


class CallerEffectTest(unittest.TestCase):
    def test_due_page_carries_timer(self):
        _tmp, db, _s, _out = make_module("focustimer due")
        body = handler_for(db).due_html()
        self.assertIn(f"id='{mod.SECTION_ANCHOR}'", body)

    def test_timer_follows_queue(self):
        _tmp, db, _s, _out = make_module("focustimer follows")
        body = handler_for(db).due_html()
        # Fixture queue is short: every due card is covered.
        self.assertIn("block covers", body)


if __name__ == "__main__":
    unittest.main()
