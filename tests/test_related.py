"""Related modules (I-23): same repo or shared concept names."""
import unittest

from groundwork import related as relmod
from groundwork import tour as tourmod

from test_web import handler_for, make_module


class RelatedTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("rel mod")
        self.mid, _ = tourmod.targets(self.db)

    def test_empty_state_has_anchor(self):
        out = relmod.related_html(self.db, self.mid)
        self.assertIn("id='related'", out)
        self.assertIn("No related modules yet", out)

    def test_same_repo_module_links(self):
        self.server.tool_create_learning_module(
            {"repo_path": str(self.tmp), "task_summary": "rel mod two"})
        out = relmod.related_html(self.db, self.mid)
        self.assertIn("rel mod two", out)

    def test_module_page_carries_section(self):
        out = handler_for(self.db).module_html(self.mid)
        self.assertIn("id='related'", out)


if __name__ == "__main__":
    unittest.main()
