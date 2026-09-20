"""Docs freshness: README + docs/ match the tour registry."""
import unittest

from groundwork import docs as docsmod
from groundwork import tour as tourmod


class DocsFreshnessTest(unittest.TestCase):
    def test_render_all_is_clean(self):
        self.assertEqual(docsmod.render_all(), [])

    def test_registry_kinds_covered_in_catalog(self):
        body = docsmod.features_doc()
        for kind, heading in docsmod.KINDS:
            self.assertIn(f"## {heading}", body)
        for e in tourmod.ENTRIES:
            self.assertIn(e["title"], body)


if __name__ == "__main__":
    unittest.main()
