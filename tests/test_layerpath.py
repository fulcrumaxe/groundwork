"""Layered onboarding path from the module graph (F-154)."""
import json
import sqlite3
import unittest

from groundwork import layerpath as mod

from test_web import handler_for, make_module


def _lessons():
    return [
        {"concept_id": "nA", "name": "A", "needs": []},
        {"concept_id": "nB", "name": "B", "needs": ["A"]},
        {"concept_id": "nC", "name": "C", "needs": ["B"]},
    ]


def _map(lessons):
    return {L["concept_id"]: L for L in lessons}


class LayersTest(unittest.TestCase):
    def test_entry_points_first(self):
        self.assertEqual(mod.layers_for(_map(_lessons())),
                         [["A"], ["B"], ["C"]])

    def test_parallel_lessons_share_layer(self):
        lessons = _map([
            {"concept_id": "nA", "name": "A", "needs": []},
            {"concept_id": "nD", "name": "D", "needs": ["A"]},
            {"concept_id": "nE", "name": "E", "needs": ["A"]},
        ])
        layers = mod.layers_for(lessons)
        self.assertEqual(layers[0], ["A"])
        self.assertEqual(layers[1], ["D", "E"])

    def test_cycle_terminates_deterministically(self):
        fwd = _map([
            {"concept_id": "nA", "name": "A", "needs": ["B"]},
            {"concept_id": "nB", "name": "B", "needs": ["A"]},
        ])
        rev = _map([
            {"concept_id": "nB", "name": "B", "needs": ["A"]},
            {"concept_id": "nA", "name": "A", "needs": ["B"]},
        ])
        self.assertEqual(mod.layers_for(fwd), [["A", "B"]])
        self.assertEqual(mod.layers_for(fwd), mod.layers_for(rev))

    def test_unknown_needs_ignored(self):
        lessons = _map([
            {"concept_id": "nA", "name": "A", "needs": ["ghost"]},
            {"concept_id": "nB", "name": "B", "needs": []},
        ])
        self.assertEqual(mod.layers_for(lessons), [["A", "B"]])

    def test_hostile_input_never_raises(self):
        for bad in (None, "x", 5, [], {}, {"n": "junk"}):
            self.assertEqual(mod.layers_for(bad), [])
            self.assertEqual(mod.starthere_html(bad), "")


class PathTest(unittest.TestCase):
    def test_flat_is_prereqs_first_with_next(self):
        path = mod.layered_path(_map(_lessons()))
        self.assertEqual([s["name"] for s in path["flat"]], ["A", "B", "C"])
        self.assertEqual(path["next"], "A")

    def test_done_marks_owned(self):
        path = mod.layered_path(_map(_lessons()), {"m:nA": (2, True)})
        self.assertEqual(path["next"], "B")
        self.assertTrue(path["flat"][0]["done"])
        self.assertFalse(path["flat"][1]["done"])


class CallerEffectTest(unittest.TestCase):
    def _seed(self, db, mid, lessons):
        con = sqlite3.connect(db)
        try:
            con.execute("UPDATE modules SET lessons=? WHERE id=?",
                        (json.dumps(lessons), mid))
            con.commit()
        finally:
            con.close()

    def test_newcomer_sees_foundations_before_dependents(self):
        """Behavioral effect: module page gains an ordered Start-here."""
        tmp, db, server, out = make_module("layerpath mod")
        self._seed(db, out["module_id"], _lessons())
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("id='start-here'", body)
        self.assertIn("Week 1", body)
        self.assertLess(body.index("#lesson-na"), body.index("#lesson-nc"))

    def test_no_graph_data_renders_unchanged(self):
        """Legacy fallback: no needs declared, no block."""
        tmp, db, server, out = make_module("layerpath legacy mod")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("id='start-here'", body)
        plain = [{"concept_id": "nA", "name": "A"},
                 {"concept_id": "nB", "name": "B"}]
        self.assertEqual(mod.starthere_html(_map(plain)), "")


class ShapeTest(unittest.TestCase):
    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual((e["id"], e["kind"], e["path"], e["anchor"]),
                         ("layered-onboarding-path", "feature",
                          "/status", mod.STATUS_ANCHOR))


if __name__ == "__main__":
    unittest.main()
