"""Desirable-difficulty dial (F-55)."""
import unittest

from groundwork import diffdial as ddmod


class DiffDialTest(unittest.TestCase):
    def test_levels_shape(self):
        self.assertEqual(ddmod.LEVELS, (1, 2, 3, 4, 5))
        self.assertEqual(ddmod.dial_params(1)["label"], "gentle")
        self.assertEqual(ddmod.dial_params(5)["label"], "spicy")
        for lv in range(1, 6):
            p = ddmod.dial_params(lv)
            self.assertEqual(set(p), {"level", "retrievability_floor",
                                      "new_cards", "label"})
            self.assertEqual(p["level"], lv)
            self.assertIsInstance(p["retrievability_floor"], float)
            self.assertIsInstance(p["new_cards"], int)
            self.assertIsInstance(p["label"], str)
            self.assertGreater(p["retrievability_floor"], 0.0)
            self.assertLessEqual(p["retrievability_floor"], 1.0)
            self.assertGreaterEqual(p["new_cards"], 0)

    def test_clamp_out_of_range_then_default(self):
        default = ddmod.dial_params(3)
        for bad in (0, 6, -1, 99, 2.5 + 99, True, False):
            self.assertEqual(ddmod.dial_params(bad), default)

    def test_garbage_then_default_never_raises(self):
        default = ddmod.dial_params(3)
        for bad in (None, "hard", "", object(), [], {}, float("nan")):
            try:
                got = ddmod.dial_params(bad)
            except Exception as exc:  # fail: must never raise
                self.fail(f"dial_params({bad!r}) raised {exc!r}")
            self.assertEqual(got, default)

    def test_monotonic_new_cards(self):
        news = [ddmod.dial_params(lv)["new_cards"] for lv in range(1, 6)]
        for a, b in zip(news, news[1:]):
            self.assertLessEqual(a, b)
        self.assertLess(news[0], news[-1])

    def test_floors_decrease_with_level(self):
        floors = [ddmod.dial_params(lv)["retrievability_floor"]
                  for lv in range(1, 6)]
        for a, b in zip(floors, floors[1:]):
            self.assertGreaterEqual(a, b)
        self.assertGreater(floors[0], floors[-1])

    def test_describe_names_bloom_tiers(self):
        text = ddmod.describe(ddmod.dial_params(5))
        self.assertIn("spicy", text.lower())
        self.assertTrue(any(t in text.lower() for t in
                            ("recall", "explain", "apply", "analyse",
                             "modify", "evaluate", "create")))
        for lv in range(1, 6):
            text = ddmod.describe(ddmod.dial_params(lv))
            self.assertIn(ddmod.dial_params(lv)["label"], text.lower())
            # Level, label, floor, and tiers stay mutually consistent.
            self.assertIn(f"(level {lv})", text)

    def test_describe_garbage_never_raises(self):
        for bad in (None, "x", object(), {}, {"level": "spicy"}):
            try:
                text = ddmod.describe(bad)
            except Exception as exc:
                self.fail(f"describe({bad!r}) raised {exc!r}")
            self.assertIsInstance(text, str)
            self.assertTrue(text.strip())

    def test_section_html_anchor(self):
        html = ddmod.section_html()
        self.assertIn("id='status-b12-diffdial'", html)
        self.assertIn("diffdial", html)

    def test_tour_entry_shape(self):
        e = ddmod.tour_entry()
        self.assertEqual(e, {"id": "difficulty-dial", "kind": "feature",
                             "title": "Difficulty dial",
                             "blurb": e["blurb"],
                             "path": "/status",
                             "anchor": "status-b12-diffdial"})
        self.assertTrue(e["blurb"])

    def test_module_constraints(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "diffdial.py").read_text(encoding="utf-8")
        self.assertNotIn("from groundwork", src)
        self.assertNotIn("import groundwork", src)
        lines = src.count("\n") + 1
        self.assertLess(lines, 350)
        for marker in ("[REDACTED]", "TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
