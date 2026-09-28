"""On-call prep packs: service-scoped weakest-first recap (F-185)."""
import copy
import os
import sqlite3
import unittest

from groundwork import emoji as emojimod
from groundwork import oncallpack as mod
from test_web import handler_for, make_module


def _concept(cid, mastery, name="c", mid="m1"):
    return {"id": cid, "name": f"{name}-{cid}", "module_id": mid,
            "mastery": mastery}


REPOS = {"m1": "/repo/payments-api", "m2": "/repo/search-web"}


def _service_of(db):
    con = sqlite3.connect(db)
    try:
        repo = con.execute("SELECT repo FROM modules").fetchone()[0]
    finally:
        con.close()
    assert repo, "fixture module must carry a repo for ?service="
    return os.path.basename(repo)


class OncallpackUnitTest(unittest.TestCase):
    def test_weakest_first_within_service(self):
        concepts = [_concept("a", 0.9), _concept("b", 0.2),
                    _concept("c", 0.2)]
        due = [{"concept_id": "b", "due": "2026-09-20T00:00:00Z"},
               {"concept_id": "c", "due": "2026-09-10T00:00:00Z"}]
        picks = mod.pick_pack(concepts, due, "payments", REPOS)
        self.assertEqual([p["concept_id"] for p in picks], ["c", "b", "a"])

    def test_other_service_and_unmapped_modules_stay_out(self):
        concepts = [_concept("a", 0.1, mid="m1"),
                    _concept("b", 0.0, mid="m2"),
                    _concept("c", 0.0, mid="m9")]
        picks = mod.pick_pack(concepts, [], "payments", REPOS)
        self.assertEqual([p["concept_id"] for p in picks], ["a"])

    def test_substring_is_case_insensitive(self):
        concepts = [_concept("a", 0.1, mid="m1")]
        self.assertEqual(len(mod.pick_pack(concepts, [], "PAYMENTS", REPOS)), 1)
        self.assertEqual(len(mod.pick_pack(concepts, [], "pay", REPOS)), 1)

    def test_empty_unknown_and_hostile_service_is_empty(self):
        concepts = [_concept("a", 0.1, mid="m1")]
        for svc in ("", "   ", "nope-service", None, 123, ["x"]):
            self.assertEqual(mod.pick_pack(concepts, [], svc, REPOS), [])
            self.assertEqual(mod.pack_html(concepts, [], svc, REPOS), "")
        self.assertEqual(mod.prep_html(":memory:", ""), "")
        self.assertEqual(mod.prep_html(":memory:", None), "")

    def test_cap_and_hostile_size(self):
        concepts = [_concept(str(i), 0.1) for i in range(5)]
        repos = {"m1": "/repo/svc"}
        self.assertEqual(len(mod.pick_pack(concepts, [], "svc", repos,
                                           size=2)), 2)
        self.assertEqual(len(mod.pick_pack(concepts, [], "svc", repos,
                                           size=99)), 5)
        self.assertEqual(len(mod.pick_pack(concepts, [], "svc", repos,
                                           size="junk")), 5)

    def test_dedupe_skips_non_dicts_and_freezes_input(self):
        concepts = [_concept("a", 0.1), "junk", None, _concept("a", 0.9)]
        before = copy.deepcopy(concepts)
        picks = mod.pick_pack(concepts, [], "payments", REPOS)
        self.assertEqual([p["concept_id"] for p in picks], ["a"])
        self.assertEqual(concepts, before)

    def test_empty_pool_is_empty(self):
        self.assertEqual(mod.pick_pack([], [], "payments", REPOS), [])
        self.assertEqual(mod.pack_html([], [], "payments", REPOS), "")
        self.assertEqual(mod.pack_html(None, None, "payments", REPOS), "")
        self.assertEqual(mod.pack_html("junk", [], "payments", REPOS), "")

    def test_html_has_study_links_reasons_and_clear(self):
        out = mod.pack_html([_concept("a", 0.2, "loops", "m9")],
                            [{"concept_id": "a",
                              "due": "2026-09-01T00:00:00Z"}],
                            "payments", {"m9": "/repo/payments-api"})
        self.assertIn("id='oncallpack'", out)
        self.assertIn("On-call prep: payments", out)
        self.assertIn("/modules/m9#lesson-", out)
        self.assertIn("mastery 0.20", out)
        self.assertIn("Study", out)
        self.assertIn("Clear service", out)

    def test_service_label_is_escaped(self):
        out = mod.pack_html([_concept("a", 0.1)], [], "pay<x>",
                            {"m1": "/repo/pay<x>"})
        self.assertIn("pay&lt;x&gt;", out)
        self.assertNotIn("pay<x>", out)

    def test_repos_for_never_raises(self):
        self.assertEqual(mod.repos_for(""), {})
        self.assertEqual(mod.repos_for(None), {})
        self.assertEqual(mod.repos_for("/nonexistent/gw.db"), {})


class OncallpackEffectTest(unittest.TestCase):
    def test_caller_due_gains_pack_when_scoped(self):
        _tmp, db, _server, _out = make_module("oncall mod")
        body = handler_for(db).due_html(service=_service_of(db))
        self.assertIn("id='oncallpack'", body)

    def test_legacy_no_param_path_has_no_pack(self):
        _tmp, db, _server, _out = make_module("oncall legacy mod")
        body = handler_for(db).due_html()
        self.assertNotIn("id='oncallpack'", body)
        self.assertNotIn("?service=", body)
        self.assertIn("id='preptrack'", body)  # global track remains

    def test_unknown_service_falls_back_to_global_track(self):
        _tmp, db, _server, _out = make_module("oncall unknown mod")
        body = handler_for(db).due_html(service="no-such-service-zzz")
        self.assertNotIn("id='oncallpack'", body)
        self.assertIn("id='preptrack'", body)


class OncallpackShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual((e["id"], e["kind"], e["path"], e["anchor"]),
                         ("oncall-prep-pack", "feature",
                          "/status", mod.STATUS_ANCHOR))

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
