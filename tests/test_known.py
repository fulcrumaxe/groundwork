"""Already-know skips (I-133): skip the line, verify in 30 days."""
import unittest

from groundwork import db as dbmod
from groundwork import known as knownmod
from groundwork import tour as tourmod

from test_web import handler_for, make_module


class KnownTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("known mod")
        dbmod.init_db(self.db)
        self.mid, _ = tourmod.targets(self.db)
        con = dbmod.connect(self.db)
        try:
            self.cid = con.execute(
                "SELECT id FROM concepts WHERE module_id=? LIMIT 1",
                (self.mid,)).fetchone()[0]
        finally:
            con.close()

    def test_skip_pushes_cards_and_records(self):
        self.assertIn("error", knownmod.skip(self.db, "nope"))
        out = knownmod.skip(self.db, self.cid)
        self.assertNotIn("error", out)
        self.assertEqual(out["module_id"], self.mid)
        con = dbmod.connect(self.db)
        try:
            dues = [r[0] for r in con.execute(
                "SELECT due FROM cards WHERE concept_id=?", (self.cid,))]
            pending = knownmod.pending(self.db, [self.cid])
        finally:
            con.close()
        self.assertTrue(dues)
        self.assertTrue(all(d >= out["verify_due"] for d in dues))
        self.assertEqual(pending[self.cid], out["verify_due"])

    def test_button_becomes_state(self):
        btn = knownmod.button_html(self.cid, "", "/m", anchor=True)
        self.assertIn("id='already-know'", btn)
        self.assertIn("/known", btn)
        out = knownmod.skip(self.db, self.cid)
        state = knownmod.button_html(self.cid, out["verify_due"], "/m",
                                     anchor=True)
        self.assertIn("id='already-know'", state)
        self.assertIn("come due then", state)

    def test_module_page_carries_button(self):
        out = handler_for(self.db).module_html(self.mid)
        self.assertIn("id='already-know'", out)


if __name__ == "__main__":
    unittest.main()
