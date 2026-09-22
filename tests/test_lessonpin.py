"""Pinned lessons (I-117)."""
import unittest

from groundwork import lessonpin as lpmod


def _rows():
    return [{"cid": "m:a", "name": "a"}, {"cid": "m:b", "name": "b"},
            {"cid": "m:c", "name": "c"}]


class NormalizePinsTest(unittest.TestCase):
    def test_dedupe_and_drop(self):
        self.assertEqual(lpmod.normalize_pins(["b", "b", " ", 7, None]), ["b"])
        self.assertEqual(lpmod.normalize_pins(None), [])
        self.assertEqual(lpmod.normalize_pins("b"), [])
        self.assertEqual(lpmod.normalize_pins(42), [])


class OrderWithPinsTest(unittest.TestCase):
    def test_empty_pins_keep_order_and_copy(self):
        rows = _rows()
        out = lpmod.order_with_pins(rows, [])
        self.assertEqual([r["name"] for r in out], ["a", "b", "c"])
        self.assertIsNot(out, rows)
        self.assertEqual(lpmod.order_with_pins(rows, None), rows)

    def test_pinned_node_first(self):
        out = lpmod.order_with_pins(_rows(), ["m:b"])
        self.assertEqual([r["name"] for r in out], ["b", "a", "c"])

    def test_pin_order_wins_and_unknown_ignored(self):
        out = lpmod.order_with_pins(_rows(), ["m:c", "m:a", "m:zzz"])
        self.assertEqual([r["name"] for r in out], ["c", "a", "b"])

    def test_hostile_never_raises(self):
        self.assertEqual(lpmod.order_with_pins(None, ["b"]), [])
        self.assertEqual(lpmod.order_with_pins("nope", ["b"]), [])
        self.assertEqual([r["name"] for r in lpmod.order_with_pins(_rows(), 42)],
                         ["a", "b", "c"])


class MarkerTest(unittest.TestCase):
    def test_unpinned_is_empty(self):
        self.assertEqual(lpmod.pin_marker_html({"name": "a"}, []), "")

    def test_pinned_chip_escaped(self):
        out = lpmod.pin_marker_html({"cid": "m:<b>", "name": "<b>"}, ["m:<b>"])
        self.assertIn("Pinned", out)
        self.assertNotIn("<b>", out)


class CallerEffectTest(unittest.TestCase):
    def test_module_html_legacy_without_pins(self):
        from test_web import handler_for, make_module
        tmp, db, server, out = make_module()
        h = handler_for(db)
        base = h.module_html(out["module_id"])
        self.assertNotIn("Pinned", base)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{lpmod.STATUS_ANCHOR}'",
                      lpmod.section_html())
        self.assertNotIn("<style", lpmod.pin_css())
        e = lpmod.tour_entry()
        self.assertEqual(e["id"], "pinned-lessons")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], lpmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
