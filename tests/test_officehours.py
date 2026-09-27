"""Office-hours bring-list fed by confusing flags (F-178)."""
import unittest

from groundwork import confusing as confmod
from groundwork import db as dbmod
from groundwork import officehours as mod

from test_web import handler_for, make_module


def _cid_mid(db, mid):
    con = dbmod.connect(db)
    try:
        return con.execute(
            "SELECT id FROM concepts WHERE module_id=? LIMIT 1",
            (mid,)).fetchone()[0]
    finally:
        con.close()


def _seed(db, cid, blocks, base_day=10):
    """Flag blocks with ascending flagged_at (first = oldest)."""
    for i, blk in enumerate(blocks):
        key = f"{cid}#{blk}"
        assert "module_id" in confmod.record(db, key, "1"), key
        con = dbmod.connect(db)
        try:
            con.execute("UPDATE confusing_flags SET flagged_at=?"
                        " WHERE section_id=?",
                        (f"2020-01-{base_day + i:02d}T00:00:00Z", key))
            con.commit()
        finally:
            con.close()
    return [f"{cid}#{b}" for b in blocks]


class ParseTest(unittest.TestCase):
    def test_key_shape(self):
        self.assertEqual(mod.parse_section("m1:calc.py:add#what-it-does"),
                         ("m1:calc.py:add", "what-it-does"))

    def test_hostile_yields_blanks(self):
        for bad in (None, "", "no-hash", "#blk", "cid#",
                    "nocolon#blk", 5, ["x"]):
            self.assertEqual(mod.parse_section(bad), ("", ""))
            self.assertEqual(mod.module_of(bad), "")
        self.assertEqual(mod.module_of("m1:calc.py:add#what-it-does"),
                         "m1")

    def test_label_words(self):
        self.assertEqual(mod.label_for("m:c#what-it-does"), "what it does")
        self.assertEqual(mod.label_for("m:c#worked_example"), "worked example")
        self.assertEqual(mod.label_for(None), "a flagged section")


class OrderTest(unittest.TestCase):
    def test_oldest_first(self):
        rows = [("b", "2020-01-02T00:00:00Z"),
                ("a", "2020-01-01T00:00:00Z")]
        self.assertEqual(mod.order_flags(rows), ["a", "b"])

    def test_ties_break_by_section(self):
        rows = [("b", "2020-01-01T00:00:00Z"),
                ("a", "2020-01-01T00:00:00Z")]
        self.assertEqual(mod.order_flags(rows), ["a", "b"])

    def test_hostile_rows_skipped(self):
        rows = [("a", "2020-01-01T00:00:00Z"), None, ("", "x"),
                ("broken",), ("b", None)]
        self.assertEqual(mod.order_flags(rows), ["b", "a"])

    def test_hostile_input_empty(self):
        for bad in (None, {}, "x", 5):
            self.assertEqual(mod.order_flags(bad), [])


class BringTest(unittest.TestCase):
    def test_empty_db_empty_list(self):
        _tmp, db, _server, _out = make_module("officehours empty mod")
        self.assertEqual(mod.bring_list(db), [])
        self.assertEqual(mod.queue_count(db), 0)

    def test_hostile_db_empty(self):
        self.assertEqual(mod.bring_list("/no/such/db.sqlite"), [])
        self.assertEqual(mod.bring_list(None), [])
        self.assertEqual(mod.queue_count(None), 0)
        self.assertEqual(mod.bring_list("x", 0), [])
        self.assertEqual(mod.bring_list("x", -3), [])

    def test_priority_and_cap(self):
        _tmp, db, _server, out = make_module("officehours queue mod")
        mid = out["module_id"]
        cid = _cid_mid(db, mid)
        keys = _seed(db, cid, [f"block-{i}" for i in range(7)])
        items = mod.bring_list(db)
        self.assertEqual(len(items), 5)
        self.assertEqual([i["section"] for i in items], keys[:5])
        self.assertEqual(items[0]["mid"], mid)
        self.assertEqual(items[0]["cid"], cid)
        self.assertEqual(items[0]["label"], "block 0")
        self.assertEqual(mod.queue_count(db), 7)
        self.assertEqual(len(mod.bring_list(db, limit=2)), 2)

    def test_unflag_leaves_queue(self):
        _tmp, db, _server, out = make_module("officehours unflag mod")
        mid = out["module_id"]
        cid = _cid_mid(db, mid)
        keys = _seed(db, cid, ["alpha", "beta"])
        confmod.record(db, keys[0], "0")
        items = mod.bring_list(db)
        self.assertEqual([i["section"] for i in items], [keys[1]])


class RenderTest(unittest.TestCase):
    def test_empty_is_legacy_fallback(self):
        self.assertEqual(mod.bring_html(""), "")
        self.assertEqual(mod.bring_html(None), "")
        _tmp, db, _server, _out = make_module("officehours render mod")
        self.assertEqual(mod.bring_html(db), "")

    def test_lists_oldest_first_with_links(self):
        _tmp, db, _server, out = make_module("officehours links mod")
        mid = out["module_id"]
        cid = _cid_mid(db, mid)
        _seed(db, cid, ["what-it-does", "worked-example"])
        body = mod.bring_html(db)
        self.assertIn("id='officehours'", body)
        self.assertIn("Bring to office hours", body)
        self.assertIn(f"/modules/{mid}", body)
        self.assertLess(body.index("what it does"),
                        body.index("worked example"))

    def test_overflow_line(self):
        _tmp, db, _server, out = make_module("officehours overflow mod")
        mid = out["module_id"]
        cid = _cid_mid(db, mid)
        _seed(db, cid, [f"block-{i}" for i in range(7)])
        body = mod.bring_html(db)
        self.assertIn("...and 2 more flagged.", body)

    def test_hostile_never_raises(self):
        self.assertEqual(mod.bring_html("/no/such/db.sqlite"), "")

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_tour_entry_shape(self):
        # Parent fix: tour targets the always-rendered Status section
        # (the live box needs flags the tour fixture lacks).
        self.assertEqual(mod.tour_entry(), {
            "id": "officehours-queue", "kind": "feature",
            "title": "Office-hours bring-list",
            "blurb": ("Your flagged sections, longest-confused first -- "
                      "bring these to office hours."),
            "path": "/status", "anchor": mod.STATUS_ANCHOR})


class CallerEffectTest(unittest.TestCase):
    def test_due_page_legacy_without_flags(self):
        _tmp, db, _server, _out = make_module("bringlist caller mod")
        plain = handler_for(db).due_html()
        self.assertNotIn("id='officehours'", plain)
        self.assertNotIn("Bring to office hours", plain)

    def test_due_page_carries_bring_list(self):
        _tmp, db, _server, out = make_module("officehours due mod")
        mid = out["module_id"]
        cid = _cid_mid(db, mid)
        _seed(db, cid, ["what-it-does"])
        flagged = handler_for(db).due_html()
        self.assertIn("id='officehours'", flagged)
        self.assertIn("what it does", flagged)
        self.assertIn(f"/modules/{mid}", flagged)


if __name__ == "__main__":
    unittest.main()
