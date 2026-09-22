"""Batch 17: surface integrations (F-54/55/56/50).

Quests render locked/unlocked skills from live mastery, the
difficulty dial shapes the Due queue and minisession, cold-attempt
rounds open from ?mode=cold, and the type contract is CI-gated over
a registry derived from the real code.
"""
import unittest

from groundwork import contractaudit as auditmod
from groundwork import diffdial as dialmod
from groundwork import exercises as exmod
from groundwork import minisession as minimod
from groundwork import quests as questsmod
from groundwork import typecontract as tcmod

from test_web import handler_for, make_module


def _rows():
    return [{"cid": "m:add", "name": "add"},
            {"cid": "m:total", "name": "total"}]


def _lesson_map():
    return {"add": {"callees": ["total"]}, "total": {"callees": []}}


class QuestViewTest(unittest.TestCase):
    def test_locked_path_from_live_mastery(self):
        body = questsmod.skills_view(_rows(), _lesson_map(),
                                     {"add": 0.1, "total": 0.9})
        self.assertIn("1 of 2 skills unlocked", body)
        self.assertIn("quest-unlocked", body)
        self.assertIn("quest-locked", body)
        self.assertIn("locked — next: add", body)

    def test_all_owned_renders_unlocked(self):
        body = questsmod.skills_view(_rows(), _lesson_map(),
                                     {"add": 0.95, "total": 0.9})
        self.assertIn("2 of 2 skills unlocked", body)
        self.assertNotIn("quest-locked", body)

    def test_empty_and_hostile_render_nothing(self):
        self.assertEqual(questsmod.skills_view([], {}, {}), "")
        self.assertEqual(questsmod.skills_view(None), "")
        self.assertEqual(questsmod.skills_view("nope"), "")

    def test_module_page_shows_quests(self):
        _tmp, db, _server, out = make_module("batch17 quests page")
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("Unlock quests", body)
        self.assertIn("skills unlocked", body)


class DialQueueTest(unittest.TestCase):
    def test_absent_dial_returns_legacy_queue(self):
        due = [{"id": "a", "stability": 1.0, "due": "2026-09-21T12:00:00Z"},
               {"id": "b", "stability": 1.0, "due": "2026-09-21T12:00:00Z"}]
        self.assertEqual(minimod.apply_dial(due, None, {}), due)
        self.assertEqual(minimod.apply_dial(due, "", {}), due)
        self.assertEqual([c["id"] for c in due], ["a", "b"])

    def test_gentle_caps_new_cards(self):
        due = [{"id": f"c{i}", "stability": 1.0,
                "due": "2026-09-21T12:00:00Z"} for i in range(5)]
        gentle = minimod.apply_dial(due, "1", {})
        self.assertEqual([c["id"] for c in gentle], ["c0"])
        spicy = minimod.apply_dial(due, "5", {})
        self.assertEqual(len(spicy), 5)

    def test_floor_drops_forgotten_reviews(self):
        # R = (1 + 10/18)^-1 ~= 0.64: below gentle/steady/balanced,
        # kept by bold (0.6).
        card = {"id": "r", "stability": 2.0, "due": "2026-09-11T12:00:00Z"}
        self.assertEqual(minimod.apply_dial([card], "1", {"r": 4}), [])
        kept = minimod.apply_dial([card], "4", {"r": 4})
        self.assertEqual([c["id"] for c in kept], ["r"])

    def test_reviewed_cards_ignore_new_cap(self):
        due = [{"id": f"c{i}", "stability": 1.0,
                "due": "2026-09-21T12:00:00Z"} for i in range(4)]
        tried = {"c0": 2, "c1": 3, "c2": 1, "c3": 5}
        kept = minimod.apply_dial(due, "1", tried)
        self.assertEqual(len(kept), 4)

    def test_control_marks_active_and_describes(self):
        box = minimod.dial_box("2", "")
        self.assertIn("(dialed)", box)
        self.assertIn("level 2", box)
        self.assertIn("/due?dial=5", box)
        self.assertIn("level 3", minimod.dial_box("garbage", ""))
        self.assertIn("mode=one&dial=2", minimod.dial_box("2", "one"))

    def test_due_page_control_and_filter(self):
        _tmp, db, _server, _out = make_module("batch17 dial page")
        h = handler_for(db)
        legacy = h.due_html()
        self.assertIn("Difficulty dial", legacy)
        self.assertIn("Card 1 of 2", legacy)
        gentle = h.due_html("auto", False, "", "1")
        self.assertIn("Card 1 of 1", gentle)
        self.assertIn("(dialed)", gentle)


class ColdRoundTest(unittest.TestCase):
    ROWS = [{"id": "m:add", "module_id": "m", "name": "add", "mastery": 0.0},
            {"id": "m:tot", "module_id": "m", "name": "total", "mastery": 0.95},
            {"id": "m:old", "module_id": "m", "name": "old", "mastery": 0.0}]

    def test_picks_unseen_not_due(self):
        body = minimod.cold_box(self.ROWS, {"m:old"})
        self.assertIn("Cold round", body)
        self.assertIn("attempt cold, then study", body)
        self.assertIn("Study add", body)
        self.assertNotIn("total", body)
        self.assertNotIn("Study old", body)

    def test_empty_pool_renders_note(self):
        body = minimod.cold_box([], set())
        self.assertIn("Cold round", body)
        self.assertIn("No unseen concepts left", body)

    def test_due_cold_mode(self):
        _tmp, db, _server, _out = make_module("batch17 cold page")
        body = handler_for(db).due_html("auto", False, "", None, True)
        self.assertIn("Cold round", body)
        self.assertIn("Full queue", body)
        self.assertNotIn("<article", body)


# Pinned F-50 baselines: exact gap sets per part. A missing set that
# SHRINKS (new branch/table row/fixture) passes; one that grows, or a
# new type missing any part, fails the gate.
# Batch 18: types 73-80 render via the generic-else widget branch by
# architecture (verified per-item effect tests); the audit cannot see
# the else, so they join the enumerated gap like earlier generic types.
# Batch 19: single-answer types (81, 87, 88) follow the generic architecture;
# Batch 20: type 89 joins them (single bound, generic widget).
# multi-line-answer types (82, 83, …) get an explicit textarea branch in
# cards.answer_widget, so the audit sees them and they leave this gap.
WIDGET_GAP = {15, 17, 26, 27, 28, 29, 31, 32, 33, 34, 35, 36, 37, 38,
              39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52,
              53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66,
              67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80,
              81, 87, 88, 89}
EMISSION_GAP = {30}
E2E_GAP = {26, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45,
           46, 47, 48, 57, 58, 59, 60, 61, 62, 63, 64}


class ContractGateTest(unittest.TestCase):
    def test_live_registry_shapes_and_holds_baseline(self):
        reg = auditmod.live_registry()
        self.assertEqual(set(reg), set(tcmod.required_parts()))
        types = set(exmod.TYPES)
        self.assertEqual(types - set(reg["generator"]), set())
        self.assertEqual(types - set(reg["grader"]), set())
        self.assertEqual(types - set(reg["disclosure"]), set())
        self.assertLessEqual(types - set(reg["widget"]), WIDGET_GAP)
        self.assertLessEqual(types - set(reg["emission"]), EMISSION_GAP)
        self.assertLessEqual(types - set(reg["e2e"]), E2E_GAP)

    def test_live_report_audits_every_type(self):
        report = auditmod.live_report()
        self.assertEqual({r["type"] for r in report}, set(exmod.TYPES))
        for r in report:
            self.assertEqual(set(r), {"type", "ok", "missing"})
        summary = tcmod.completeness(report)
        self.assertEqual(summary["total"], len(exmod.TYPES))
        self.assertEqual(summary["incomplete"], len(summary["missing_types"]))

    def test_gate_catches_a_new_bare_type(self):
        reg = auditmod.live_registry()
        reg = {part: set(s) for part, s in reg.items()}
        res = tcmod.audit_type(999, reg)
        self.assertFalse(res["ok"])
        self.assertEqual(set(res["missing"]), set(tcmod.required_parts()))


if __name__ == "__main__":
    unittest.main()
