"""Batch 18 central wiring: home module, AREAS, tour, order threading."""
import unittest

from groundwork import batch18 as b18mod
from groundwork import explainflip as flipmod
from groundwork import lessons as lesmod
from groundwork import modularity as modularitymod
from groundwork import tour as tourmod


def _worked_lesson():
    return {"concept_id": "c", "name": "add", "kind": "function",
            "file": "calc.py", "line": 1, "summary": "Adds a and b.",
            "docstring": "", "callers": [], "callees": [],
            "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
            "how": ["take a", "take b", "return total"],
            "worked": {"call": "add(2, 3)", "output": "5",
                       "trace": {"var": "total", "steps": [2, 5]}},
            "dualcode": {"steps": [], "states": []}}


B18_AREAS = ("parsons", "tokens", "pagesnap", "emoji", "motion",
             "contrast", "explainflip", "glossary", "interview",
             "transfer", "fartransfer", "pressure", "incident",
             "premortem", "fluency", "nameguess", "batch18")

B18_TOUR_IDS = ("parsons-stable", "design-tokens", "page-snapshots",
                "emoji-free-icons", "motion-budget", "high-contrast-mode",
                "explain-differently", "inline-glossary",
                "mastery-interview", "transfer-test", "far-transfer",
                "pressure-drill", "incident-replay", "pre-mortem",
                "reading-fluency", "naming-fluency")


class Batch18WiringTest(unittest.TestCase):
    def test_home_joins_sixteen_anchored_sections(self):
        html = b18mod.batch18_html()
        self.assertIn("id='status-batch18'", html)
        for area in B18_AREAS:
            if area == "batch18":
                continue
            mod = __import__(f"groundwork.{area}", fromlist=["STATUS_ANCHOR"])
            self.assertIn(f"id='{mod.STATUS_ANCHOR}'", html, area)

    def test_areas_registry_covers_batch(self):
        for area in B18_AREAS:
            self.assertIn(area, modularitymod.AREAS, area)
            self.assertEqual(modularitymod.AREAS[area], f"{area}.py")
        self.assertEqual(modularitymod.check(), [])

    def test_tour_entries_land_on_batch_anchors(self):
        html = b18mod.batch18_html()
        by_id = {e["id"]: e for e in tourmod.ENTRIES}
        for tid in B18_TOUR_IDS:
            self.assertIn(tid, by_id, tid)
            self.assertEqual(by_id[tid]["path"], "/status")
            self.assertIn(f"id='{by_id[tid]['anchor']}'", html, tid)

    def test_order_threading_flips_real_lesson_render(self):
        # Caller integration: ?order=examples reaches render_levels.
        default = lesmod.render_levels(_worked_lesson(), 0.0, 0, "2", "/",
                                       order="definition")
        flipped = lesmod.render_levels(_worked_lesson(), 0.0, 0, "2", "/",
                                       order="examples")
        self.assertIn("Worked example", default)
        self.assertLess(flipped.index("Worked example"),
                        default.index("Worked example"))
        self.assertIn("order=definition", flipped)  # toggle preserved


if __name__ == "__main__":
    unittest.main()
