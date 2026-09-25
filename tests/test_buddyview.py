"""Study-with-a-friend side-by-side view (I-143)."""
import unittest

from groundwork import buddyview as mod

from test_web import handler_for, make_module


class BuddyTest(unittest.TestCase):
    def test_solo_renders_nothing(self):
        self.assertEqual(mod.buddy_html("Loops", []), "")
        self.assertEqual(mod.buddy_html("Loops", ["Solo"]), "")
        self.assertEqual(mod.buddy_html("Loops", ["A", "A", ""]), "")

    def test_duo_renders_two_labelled_panes(self):
        body = mod.buddy_html("Loops", ["Ann", "Bo"])
        self.assertIn("buddy-view", body)
        self.assertIn("Ann", body)
        self.assertIn("Bo", body)
        self.assertEqual(body.count("buddy-pane"), 2)

    def test_markers_clamped_and_escaped(self):
        body = mod.buddy_html("L", ["A", "B"],
                              [("A", 150), ("<i>B</i>", -5), ("", 50)])
        self.assertIn("100%", body)
        self.assertIn("0%", body)
        self.assertNotIn("<i>B</i>", body)

    def test_hostile_never_raises(self):
        self.assertEqual(mod.buddy_html(None, None), "")
        self.assertEqual(mod.buddy_markers("nope"), [])
        self.assertEqual(mod.clean_name(123), "")

    def test_entry_form_shape(self):
        form = mod.entry_html("/modules/m")
        self.assertIn("buddy-entry", form)
        self.assertIn("name='buddy'", form)
        self.assertIn("/modules/m", form)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_module_page_carries_entry_form(self):
        _tmp, db, _s, out = make_module("buddyview caller")
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("buddy-entry", body)
        self.assertNotIn("buddy-view", body)

    def test_duo_query_renders_panes(self):
        _tmp, db, _s, out = make_module("buddyview duo")
        h = handler_for(db)
        body = h.module_html(out["module_id"], buddies=["Ann", "Bo"])
        self.assertIn("buddy-view", body)
        self.assertIn("Ann", body)


if __name__ == "__main__":
    unittest.main()
