"""Lesson clarity ratings (I-114): vote 1-5, average feeds authors."""
import unittest

from groundwork import clarity as claritymod
from groundwork import db as dbmod
from groundwork import tour as tourmod

from test_web import handler_for, make_module


class ClarityTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("clarity mod")
        dbmod.init_db(self.db)
        self.mid, _ = tourmod.targets(self.db)
        con = dbmod.connect(self.db)
        try:
            self.cid = con.execute(
                "SELECT id FROM concepts WHERE module_id=? LIMIT 1",
                (self.mid,)).fetchone()[0]
        finally:
            con.close()

    def test_record_and_average(self):
        self.assertIn("error", claritymod.record(self.db, "nope", 5))
        self.assertIn("error", claritymod.record(self.db, self.cid, 9))
        ok = claritymod.record(self.db, self.cid, 4)
        self.assertNotIn("error", ok)
        claritymod.record(self.db, self.cid, 2)
        self.assertEqual(claritymod.summaries(self.db, [self.cid])[self.cid],
                         (3.0, 2))

    def test_block_has_form_and_anchor(self):
        out = claritymod.block_html(self.cid, 3.0, 2, "/modules/m",
                                    anchor=True)
        self.assertIn("id='clarity'", out)
        self.assertIn("3.0/5 from 2 votes", out)
        self.assertIn(f"/concepts/{self.cid}/rate", out)

    def test_module_page_carries_clarity(self):
        out = handler_for(self.db).module_html(self.mid)
        self.assertIn("id='clarity'", out)
        self.assertIn("No clarity votes yet", out)


if __name__ == "__main__":
    unittest.main()
