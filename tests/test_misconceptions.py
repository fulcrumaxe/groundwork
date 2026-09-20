"""Misconception callouts (I-111)."""
import unittest

from groundwork import misconceptions as mcmod


class CalloutTest(unittest.TestCase):
    def test_callout_box(self):
        body = mcmod.callout("Variables hold values, not boxes.")
        self.assertIn("id='misconception'", body)
        self.assertIn("Variables hold values", body)

    def test_blank_renders_empty(self):
        self.assertEqual(mcmod.callout(""), "")
        self.assertEqual(mcmod.callout(None), "")

    def test_escapes_html(self):
        body = mcmod.callout("<script>x</script>")
        self.assertNotIn("<script>", body)


if __name__ == "__main__":
    unittest.main()
