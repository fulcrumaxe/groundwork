"""Standard button order, primary left (I-35)."""
import unittest

from groundwork import buttons as mod
from groundwork import disputes as dismod
from groundwork import reset as resetmod


class GroupTest(unittest.TestCase):
    def test_primary_first(self):
        out = mod.group("<button>Save</button>", ["<a href='/x'>Cancel</a>"])
        self.assertTrue(out.index("<button>") < out.index("<a "))

    def test_multiple_secondaries_keep_order(self):
        out = mod.group("P", ["A", "B"])
        self.assertEqual(out, "P A B")

    def test_hostile_input_never_raises(self):
        self.assertEqual(mod.group(None, None), "")
        self.assertEqual(mod.group("<button>P</button>", None), "<button>P</button>")
        self.assertIn("P", mod.group("<button>P</button>", "<a>C</a>"))
        self.assertIn("3", mod.group(3, [None, 5]))
        self.assertEqual(mod.group("", ["<a>C</a>"]), "<a>C</a>")


class AuditTest(unittest.TestCase):
    def test_ok_primary_first(self):
        html = ("<form method='post'><button>Save</button> "
                "<a href='/x'>Cancel</a></form>")
        self.assertEqual(mod.audit(html), [])

    def test_violation_secondary_first(self):
        html = ("<form method='post'><a href='/x'>Cancel</a> "
                "<button>Save</button></form>")
        found = mod.audit(html)
        self.assertEqual(len(found), 1)
        self.assertIn("secondary", found[0]["detail"])

    def test_single_button_passes(self):
        self.assertEqual(mod.audit("<form><button>Go</button></form>"), [])

    def test_hostile_input(self):
        for bad in (None, "", 42, ["<form><button>x</button></form>"]):
            self.assertEqual(mod.audit(bad), [])

    def test_type_button_counts_secondary(self):
        html = ("<form><button type='button'>Later</button>"
                "<button>Submit</button></form>")
        self.assertEqual(len(mod.audit(html)), 1)


class ComplianceTest(unittest.TestCase):
    def test_real_rendered_forms_comply(self):
        reset_html = resetmod.confirm_html("m1", "Module one")
        dispute_html = dismod.dispute_form_html("c1", "/due")
        # Representative multi-action resolve row (queue_html needs a DB).
        resolve_html = (
            "<form method='post' action='/disputes/1/resolve'>"
            "<button name='verdict' value='accepted'>Accept</button>"
            "<button name='verdict' value='rejected'>Reject</button></form>")
        for html in (reset_html, dispute_html, resolve_html):
            with self.subTest(html=html[:60]):
                self.assertEqual(mod.audit(html), [])

    def test_section_anchor(self):
        self.assertIn("id='status-b8-buttons'", mod.section_html())


if __name__ == "__main__":
    unittest.main()
