"""Accessibility-champions track: audit practice per frontend (F-191)."""
import copy
import sqlite3
import unittest

from groundwork import a11ychamp as mod
from groundwork import emoji as emojimod
from test_web import handler_for, make_module


def _row(cid, etype="52", mastery=0.2, name=None, file="groundwork/web.py",
         due="2026-09-10T00:00:00Z", mid="m1"):
    return {"card_id": f"card-{cid}-{etype}", "exercise_type": etype,
            "concept_id": cid, "name": name or f"c-{cid}", "file": file,
            "module_id": mid, "mastery": mastery, "due": due}


class A11ychampUnitTest(unittest.TestCase):
    def test_weakest_first_stalest_breaks_ties(self):
        rows = [_row("a", mastery=0.9, due="2026-09-01T00:00:00Z"),
                _row("b", mastery=0.2, due="2026-09-20T00:00:00Z"),
                _row("c", mastery=0.2, due="2026-09-10T00:00:00Z")]
        picks = mod.pick_track(rows)
        self.assertEqual([p["concept_id"] for p in picks], ["c", "b", "a"])

    def test_type52_always_in_type53_gated_on_ui(self):
        rows = [_row("backend-audit", file="groundwork/sched.py"),
                _row("css-words", etype="53", name="verdicts_css",
                     file="groundwork/verdicts.py"),
                _row("cli-words", etype="53", name="cmd_e2e",
                     file="groundwork/__main__.py"),
                _row("recall", etype="1")]
        picks = mod.pick_track(rows)
        self.assertEqual({p["concept_id"] for p in picks},
                         {"backend-audit", "css-words"})

    def test_scope_narrows_by_file_prefix(self):
        rows = [_row("a", file="groundwork/web.py"),
                _row("b", file="groundwork/verdicts.py")]
        picks = mod.pick_track(rows, scope="groundwork/verdicts")
        self.assertEqual([p["concept_id"] for p in picks], ["b"])
        self.assertEqual(mod.pick_track(rows, scope="groundwork/nope"), [])

    def test_cap_and_hostile_size(self):
        rows = [_row(str(i)) for i in range(5)]
        self.assertEqual(len(mod.pick_track(rows, size=2)), 2)
        self.assertEqual(len(mod.pick_track(rows, size=99)), 5)
        self.assertEqual(len(mod.pick_track(rows, size="junk")), 5)

    def test_dedupe_keeps_earliest_due_and_freezes_input(self):
        rows = [_row("a", mastery=0.5, due="2026-09-20T00:00:00Z"), "junk",
                None, _row("a", mastery=0.1, due="2026-09-10T00:00:00Z")]
        before = copy.deepcopy(rows)
        picks = mod.pick_track(rows)
        self.assertEqual([p["concept_id"] for p in picks], ["a"])
        self.assertEqual(picks[0]["due"], "2026-09-10T00:00:00Z")
        self.assertEqual(rows, before)

    def test_empty_is_empty(self):
        self.assertEqual(mod.pick_track([]), [])
        self.assertEqual(mod.pick_track(None), [])
        self.assertEqual(mod.champ_html(""), "")
        self.assertEqual(mod.progress("", []), {"owned": 0, "total": 0})


class A11ychampEffectTest(unittest.TestCase):
    def _db_with_audit_cards(self):
        _tmp, db, _server, out = make_module("champ mod")
        mid = out["module_id"]
        con = sqlite3.connect(db)
        try:
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file, line,"
                " mastery) VALUES(?,?,?,?,?,?,?)",
                ("champ-weak", mid, "module_html", "page",
                 "groundwork/web.py", 3, 0.1))
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file, line,"
                " mastery) VALUES(?,?,?,?,?,?,?)",
                ("champ-strong", mid, "verdicts_css", "function",
                 "groundwork/verdicts.py", 5, 0.9))
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file, line,"
                " mastery) VALUES(?,?,?,?,?,?,?)",
                ("champ-cli", mid, "cmd_e2e", "function",
                 "groundwork/__main__.py", 7, 0.0))
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type, front, back,"
                " due, stale) VALUES(?,?,?,?,?,?,0)",
                ("champ-card-52", "champ-weak", "52", "audit this",
                 "0=img-missing-alt", "2026-09-10T00:00:00Z"))
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type, front, back,"
                " due, stale) VALUES(?,?,?,?,?,?,0)",
                ("champ-card-53", "champ-strong", "53", "extract strings",
                 "Welcome", "2026-09-01T00:00:00Z"))
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type, front, back,"
                " due, stale) VALUES(?,?,?,?,?,?,0)",
                ("champ-card-cli", "champ-cli", "53", "extract strings",
                 "Usage", "2026-09-01T00:00:00Z"))
            # Owned proof for the weak concept: modify-bloom passes + return.
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type, front, back,"
                " due, stale) VALUES(?,?,?,?,?,?,0)",
                ("champ-card-own", "champ-weak", "20", "extend it",
                 "reference", "2026-09-01T00:00:00Z"))
            con.execute("INSERT INTO reviews(card_id, grade) VALUES(?,?)",
                        ("champ-card-own", 5))
            con.execute("INSERT INTO reviews(card_id, grade) VALUES(?,?)",
                        ("champ-card-own", 4))
            con.commit()
        finally:
            con.close()
        return db

    def _track_section(self, body):
        # Other Due sections (digest, party trick, recap) also name
        # concepts, so order/membership pins scope to the track box.
        seg = body.split("id='a11ychamp-track'", 1)[1]
        return seg.split("</section>", 1)[0]

    def test_caller_due_gains_champions_track(self):
        body = handler_for(self._db_with_audit_cards()).due_html()
        self.assertIn("id='a11ychamp-track'", body)
        # Weakest first despite the stalest due sitting on the strong one;
        # the non-UI i18n concept never enters the pool.
        sec = self._track_section(body)
        self.assertLess(sec.index("module_html"), sec.index("verdicts_css"))
        self.assertNotIn("cmd_e2e", sec)
        self.assertIn("1/2 owned", sec)
        self.assertIn("[a11y]", sec)
        self.assertIn("[i18n]", sec)

    def test_caller_scope_narrows_track(self):
        db = self._db_with_audit_cards()
        body = handler_for(db).due_html(scope="groundwork/verdicts")
        self.assertIn("id='a11ychamp-track'", body)
        sec = self._track_section(body)
        self.assertIn("verdicts_css", sec)
        self.assertNotIn("module_html", sec)

    def test_no_audit_cards_renders_nothing(self):
        _tmp, db, _server, _out = make_module("plain mod")
        self.assertEqual(mod.champ_html(db), "")

    def test_legacy_due_bytes_survive_without_audit_cards(self):
        _tmp, db, _server, _out = make_module("plain mod")
        body = handler_for(db).due_html()
        self.assertNotIn("id='a11ychamp-track'", body)


class A11ychampShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")
        self.assertEqual((e["path"], e["anchor"]),
                         ("/status", mod.STATUS_ANCHOR))

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())
        self.assertIn("Live now", mod.section_html("groundwork.db"))

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
