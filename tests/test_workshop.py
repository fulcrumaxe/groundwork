"""Conference workshop mode: 2-hour guided module sprints (F-195)."""
import copy
import unittest

from test_web import handler_for, make_module

from groundwork import workshop as mod


def _card(cid, due="2026-09-20T00:00:00Z", attempts=2, lapses=0,
          stability=1.0, difficulty=2):
    return {"id": cid, "due": due, "attempts": attempts, "lapses": lapses,
            "stability": stability, "difficulty": difficulty}


def _due(n=10):
    return [_card(f"c{i:02d}") for i in range(n)]


class ParseTest(unittest.TestCase):
    def test_default_is_guided_120(self):
        self.assertEqual(mod.parse_workshop(""), ("guided", 120))
        self.assertEqual(mod.parse_workshop(None), ("guided", 120))
        self.assertEqual(mod.parse_workshop(), ("guided", 120))

    def test_modes_and_lengths(self):
        self.assertEqual(mod.parse_workshop("self"), ("self", 120))
        self.assertEqual(mod.parse_workshop("guided-60"), ("guided", 60))
        self.assertEqual(mod.parse_workshop("self-90"), ("self", 90))
        self.assertEqual(mod.parse_workshop("90"), ("guided", 90))
        self.assertEqual(mod.parse_workshop("SOLO-30"), ("self", 30))

    def test_hostile_falls_back(self):
        self.assertEqual(mod.parse_workshop("junk"), ("guided", 120))
        self.assertEqual(mod.parse_workshop("junk-60"), ("guided", 120))
        self.assertEqual(mod.parse_workshop("guided-45"), ("guided", 120))
        self.assertEqual(mod.parse_workshop(["self"]), ("guided", 120))


class AgendaTest(unittest.TestCase):
    def test_four_segments_weakest_first(self):
        lapses = [3, 0, 5, 1, 4, 2, 0, 1]
        due = [_card(f"c{i:02d}", lapses=l) for i, l in enumerate(lapses)]
        agenda = mod.agenda_for(due, estimate_fn=lambda c: 60)
        self.assertEqual((agenda["mode"], agenda["minutes"]), ("guided", 120))
        self.assertTrue(agenda["intro"])
        segs = agenda["segments"]
        self.assertEqual(len(segs), 4)
        self.assertEqual([s["minutes"] for s in segs], [25, 25, 25, 25])
        self.assertEqual([s["break_after"] for s in segs],
                         [True, True, True, False])
        # Weakest cards (most lapses) open the sprint.
        self.assertEqual(segs[0]["cards"], ["c02", "c04"])
        self.assertEqual(segs[3]["cards"], ["c01", "c06"])

    def test_stability_breaks_lapse_ties(self):
        due = [_card("steady", stability=30.0), _card("frail", stability=1.0)]
        agenda = mod.agenda_for(due, estimate_fn=lambda c: 60)
        segs = agenda["segments"]
        self.assertEqual([s["cards"] for s in segs], [["frail"], ["steady"]])

    def test_lengths_scale_segments(self):
        self.assertEqual(len(mod.agenda_for(
            _due(8), "guided-60", estimate_fn=lambda c: 60)["segments"]), 2)
        short = mod.agenda_for(_due(8), "self-30", estimate_fn=lambda c: 60)
        self.assertEqual(len(short["segments"]), 1)
        self.assertFalse(short["intro"])
        self.assertEqual(short["segments"][0]["minutes"], 30)
        self.assertEqual(len(mod.agenda_for(
            _due(8), "guided-90", estimate_fn=lambda c: 60)["segments"]), 3)

    def test_empty_queue_yields_no_segments(self):
        for bad in ([], None, "nope"):
            agenda = mod.agenda_for(bad)
            self.assertEqual(agenda["segments"], [])
            self.assertEqual((agenda["mode"], agenda["minutes"]),
                             ("guided", 120))

    def test_hostile_never_raises(self):
        agenda = mod.agenda_for(_due(3), workshop="junk-99",
                                estimate_fn="junk")
        self.assertEqual((agenda["mode"], agenda["minutes"]),
                         ("guided", 120))
        self.assertIn(mod.SECTION_ANCHOR, mod.sprint_html(None))
        self.assertIn(mod.SECTION_ANCHOR, mod.sprint_html("nope"))

    def test_never_mutates_input(self):
        due = list(reversed(_due(6)))
        before = copy.deepcopy(due)
        mod.agenda_for(due, estimate_fn=lambda c: 60)
        mod.sprint_html(due, estimate_fn=lambda c: 60)
        self.assertEqual(due, before)


class SprintHtmlTest(unittest.TestCase):
    def test_guided_default_with_clocks(self):
        body = mod.sprint_html(_due(8), estimate_fn=lambda c: 60)
        self.assertIn(f"id='{mod.SECTION_ANCHOR}'", body)
        self.assertIn("120-minute guided sprint", body)
        self.assertIn("facilitator calls time", body)
        self.assertIn("Start the sprint", body)
        self.assertIn("workshop-clock", body)
        self.assertIn("data-ws-start", body)
        self.assertIn("Break \u2014 5 minutes", body)
        self.assertIn("/due?workshop=self-120", body)

    def test_self_mode_is_a_checklist(self):
        body = mod.sprint_html(_due(8), "self", estimate_fn=lambda c: 60)
        self.assertIn("own pace", body)
        self.assertIn("Segment 1 of 4", body)
        self.assertNotIn("workshop-clock", body)
        self.assertNotIn("data-ws-start", body)

    def test_empty_renders_all_clear_without_buttons(self):
        body = mod.sprint_html([])
        self.assertIn(f"id='{mod.SECTION_ANCHOR}'", body)
        self.assertIn("All clear", body)
        self.assertNotIn("Start", body)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/due")
        self.assertEqual(entry["anchor"], mod.SECTION_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_due_page_carries_workshop(self):
        _tmp, db, _s, _out = make_module("workshop due")
        due = handler_for(db).due_html()
        self.assertIn(f"id='{mod.SECTION_ANCHOR}'", due)
        self.assertIn("Workshop sprint", due)

    def test_legacy_no_param_path_is_guided_default(self):
        _tmp, db, _s, _out = make_module("workshop fallback")
        due = handler_for(db).due_html()
        # No ?workshop= param: guided 120-minute sprint is the fallback.
        self.assertIn("120-minute guided sprint", due)
        self.assertIn("facilitator calls time", due)


if __name__ == "__main__":
    unittest.main()
