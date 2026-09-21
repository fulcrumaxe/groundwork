"""Type completeness contract (F-50): audit library + status demo."""
import unittest

from groundwork import typecontract as tcmod


def _full_registry(types=(72,)):
    s = set(types)
    return {"generator": set(s), "grader": set(s), "widget": set(s),
            "disclosure": set(s), "emission": set(s), "e2e": set(s)}


class ContractShapeTest(unittest.TestCase):
    def test_required_parts_exact(self):
        self.assertEqual(tcmod.required_parts(),
                         ("generator", "grader", "widget",
                          "disclosure", "emission", "e2e"))

    def test_status_anchor(self):
        self.assertEqual(tcmod.STATUS_ANCHOR, "status-b12-typecontract")

    def test_no_groundwork_imports_stdlib_only(self):
        # No imports from the package (docstring prose may name it).
        import pathlib
        import re
        src = pathlib.Path(tcmod.__file__).read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"^\s*(import|from)\s+groundwork\b",
                                    src, re.M))
        self.assertIsNone(re.search(r"^\s*from\s+\.", src, re.M))
        self.assertLessEqual(len(src.splitlines()), 350)

    def test_tour_entry_shape(self):
        e = tcmod.tour_entry()
        self.assertEqual(e, {"id": "type-contract", "kind": "feature",
                             "title": "Type completeness contract",
                             "blurb": e["blurb"],
                             "path": "/status",
                             "anchor": "status-b12-typecontract"})
        self.assertTrue(e["blurb"])
        self.assertEqual(e["anchor"], tcmod.STATUS_ANCHOR)


class AuditTest(unittest.TestCase):
    def test_complete_registry_passes(self):
        res = tcmod.audit_type(72, _full_registry((72,)))
        self.assertEqual(res, {"type": 72, "ok": True, "missing": []})

    def test_deliberately_incomplete_registry_fails(self):
        reg = _full_registry((72,))
        reg["grader"] = set()
        reg["e2e"] = set()
        res = tcmod.audit_type(72, reg)
        self.assertFalse(res["ok"])
        self.assertEqual(res["type"], 72)
        self.assertIn("grader", res["missing"])
        self.assertIn("e2e", res["missing"])
        self.assertNotIn("generator", res["missing"])

    def test_unknown_type_fails_closed(self):
        res = tcmod.audit_type(99, _full_registry((72,)))
        self.assertFalse(res["ok"])
        self.assertEqual(len(res["missing"]), 6)

    def test_malformed_input_never_raises(self):
        for bad_reg in (None, [], "x", {}, {"generator": object()}):
            res = tcmod.audit_type(72, bad_reg)
            self.assertFalse(res["ok"])
        res = tcmod.audit_type("nope", _full_registry((72,)))
        self.assertFalse(res["ok"])
        res = tcmod.audit_type(None, None)
        self.assertFalse(res["ok"])

    def test_dict_registry_reads_as_keys(self):
        reg = _full_registry((72,))
        reg["grader"] = {72: "anything"}
        self.assertTrue(tcmod.audit_type(72, reg)["ok"])


class CompletenessTest(unittest.TestCase):
    def test_summary_counts(self):
        report = [tcmod.audit_type(72, _full_registry((72,))),
                  tcmod.audit_type(99, _full_registry((72,)))]
        s = tcmod.completeness(report)
        self.assertEqual(s["total"], 2)
        self.assertEqual(s["complete"], 1)
        self.assertEqual(s["incomplete"], 1)
        self.assertAlmostEqual(s["rate"], 0.5)
        self.assertEqual(s["missing_types"], [99])

    def test_empty_and_bad_report_fail_closed(self):
        self.assertEqual(tcmod.completeness([])["total"], 0)
        self.assertEqual(tcmod.completeness(None)["total"], 0)
        self.assertEqual(tcmod.completeness(object())["total"], 0)


class SectionHtmlTest(unittest.TestCase):
    def test_anchor_and_parts(self):
        html = tcmod.section_html()
        self.assertIn("id='status-b12-typecontract'", html)
        for p in tcmod.required_parts():
            self.assertIn(p, html)
        self.assertIn("<table", html)

    def test_live_report_renders(self):
        report = [tcmod.audit_type(72, _full_registry((72,)))]
        html = tcmod.section_html(report)
        self.assertIn("id='status-b12-typecontract'", html)
        self.assertIn("72", html)

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "typecontract.py").read_text(encoding="utf-8")
        for marker in ("[REDACTED]", "TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
