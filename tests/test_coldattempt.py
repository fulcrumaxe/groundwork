"""Productive-failure cold-attempt sessions (F-56)."""
import unittest

from groundwork import coldattempt as camod


def _concepts():
    return [
        {"id": "c1", "name": "Alpha", "module_id": "m1"},
        {"id": "c2", "name": "Beta", "module_id": "m1"},
        {"id": "c3", "name": "Gamma", "module_id": "m2"},
        {"id": "c4", "name": "Delta", "module_id": "m2"},
        {"id": "c5", "name": "Epsilon", "module_id": "m3"},
    ]


class ColdSessionTest(unittest.TestCase):
    def test_excludes_owned_and_due(self):
        res = camod.cold_session(_concepts(), owned_ids={"c1"},
                                 due_ids={"c2"}, size=10)
        got = [i["concept_id"] for i in res["items"]]
        self.assertNotIn("c1", got)
        self.assertNotIn("c2", got)
        self.assertTrue(got)
        for item in res["items"]:
            self.assertIn("concept_id", item)
            self.assertIn("attempt cold, then study", item["prime"])
        self.assertTrue(res["note"])

    def test_empty_pool_fails_closed(self):
        res = camod.cold_session(_concepts(),
                                 owned_ids={"c1", "c2", "c3", "c4", "c5"},
                                 due_ids=set())
        self.assertEqual(res["items"], [])
        self.assertTrue(res["note"])
        res2 = camod.cold_session([], owned_ids=set(), due_ids=set())
        self.assertEqual(res2["items"], [])
        self.assertTrue(res2["note"])

    def test_size_cap(self):
        res = camod.cold_session(_concepts(), owned_ids=set(),
                                 due_ids=set(), size=3)
        self.assertEqual(len(res["items"]), 3)
        res1 = camod.cold_session(_concepts(), owned_ids=set(),
                                  due_ids=set(), size=1)
        self.assertEqual(len(res1["items"]), 1)
        res_all = camod.cold_session(_concepts(), owned_ids=set(),
                                     due_ids=set(), size=99)
        self.assertEqual(len(res_all["items"]), 5)

    def test_adjacent_to_owned_first(self):
        concepts = _concepts()
        res = camod.cold_session(concepts, owned_ids={"c1"},
                                 due_ids=set(), size=10)
        got = [i["concept_id"] for i in res["items"]]
        # c2 shares m1 with owned c1, so it sorts before m2/m3 unseen.
        self.assertLess(got.index("c2"), got.index("c5"))

    def test_hostile_input_never_raises(self):
        for bad in (None, "x", 42, object()):
            res = camod.cold_session(bad, owned_ids=bad, due_ids=bad,
                                     size=bad)
            self.assertEqual(res["items"], [])
            self.assertTrue(res["note"])
        res = camod.cold_session([None, "x", {"no-id": 1}],
                                 owned_ids=None, due_ids=None)
        self.assertEqual(res["items"], [])

    def test_duplicate_ids_deduped_never_raise(self):
        concepts = _concepts() + [{"id": "c3", "name": "Gamma dup",
                                   "module_id": "m2"}]
        res = camod.cold_session(concepts, owned_ids=set(),
                                 due_ids=set(), size=10)
        got = [i["concept_id"] for i in res["items"]]
        self.assertEqual(len(got), len(set(got)))
        self.assertEqual(len(got), 5)

    def test_section_html_anchor(self):
        html = camod.section_html()
        self.assertIn("id='status-b12-coldattempt'", html)

    def test_tour_entry_shape(self):
        entry = camod.tour_entry()
        self.assertEqual(entry["id"], "cold-attempt")
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], "status-b12-coldattempt")
        self.assertTrue(entry["title"] and entry["blurb"])

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "coldattempt.py").read_text(encoding="utf-8")
        for marker in ("[REDACTED]", "TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
