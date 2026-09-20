"""Copy-link anchors (I-28)."""
import unittest

from groundwork import copylink as copymod


class CopyLinkTest(unittest.TestCase):
    def test_anchor_link(self):
        body = copymod.copy_link("Lesson One")
        self.assertIn("href='#lesson-one'", body)
        self.assertIn("copylink", body)

    def test_blank_renders_empty(self):
        self.assertEqual(copymod.copy_link(""), "")
        self.assertEqual(copymod.copy_link(None), "")

    def test_escapes_html(self):
        body = copymod.copy_link("<b>x</b>")
        self.assertNotIn("<b>", body)
        self.assertIn("b-x-b", body)


if __name__ == "__main__":
    unittest.main()
