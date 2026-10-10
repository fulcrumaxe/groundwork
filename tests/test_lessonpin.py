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


def _two_concept_db():
    """Fixture module plus a second concept+lesson; returns (db, mid)."""
    import json
    import sqlite3

    from test_web import make_module
    tmp, db, server, out = make_module()
    mid = out["module_id"]
    con = sqlite3.connect(db)
    try:
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file, line,"
            " mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (f"{mid}:mul", mid, "mul", "function", "calc.py", 5, 0.0))
        lessons = json.loads(con.execute(
            "SELECT lessons FROM modules WHERE id=?", (mid,)).fetchone()[0])
        lessons.append({"concept_id": "mul", "name": "mul", "kind": "function",
                        "file": "calc.py", "line": 5,
                        "summary": "mul() multiplies two numbers.",
                        "docstring": "", "callers": [], "callees": [],
                        "key_lines": "",
                        "source": "def mul(a, b):\n    return a * b\n",
                        "how": ["Read the factors."], "worked": None})
        con.execute("UPDATE modules SET lessons=? WHERE id=?",
                    (json.dumps(lessons), mid))
        con.commit()
    finally:
        con.close()
    return db, mid


class CallerEffectTest(unittest.TestCase):
    def test_module_html_legacy_without_pins(self):
        from test_web import handler_for, make_module
        tmp, db, server, out = make_module()
        h = handler_for(db)
        base = h.module_html(out["module_id"])
        self.assertNotIn("Pinned", base)

    def test_module_html_pins_reorder_and_mark(self):
        from test_web import handler_for
        db, mid = _two_concept_db()
        h = handler_for(db)
        base = h.module_html(mid)
        add_sec = "<section id='lesson-calc-py-add'>"
        mul_sec = "<section id='lesson-mul'>"
        self.assertLess(base.index(add_sec), base.index(mul_sec))
        pinned = h.module_html(mid, pins=["mul"])
        self.assertLess(pinned.index(mul_sec), pinned.index(add_sec))
        self.assertIn("class='pin'", pinned)
        self.assertIn("Pinned", pinned)

    def test_module_html_unknown_pins_keep_legacy(self):
        from test_web import handler_for
        db, mid = _two_concept_db()
        h = handler_for(db)
        base = h.module_html(mid)
        self.assertEqual(h.module_html(mid, pins=["zzz"]), base)
        self.assertEqual(h.module_html(mid, pins=None), base)

    def test_pin_css_shipped_in_page_css(self):
        from groundwork import web as webmod
        self.assertIn(".pin{", webmod.CSS)
        self.assertIn(lpmod.pin_css(), webmod.CSS)

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
