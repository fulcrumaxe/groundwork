"""Circular lesson dependencies: deterministic tie-break (I-132)."""
import unittest

from groundwork import depcycle as depmod
from groundwork import select as selmod


def _scored(node_id, name="n"):
    return selmod.ScoredConcept(node_id, name, "function", "a.py", 1,
                                1.0, 1.0, 1.0, 1.0)


class FindCyclesTest(unittest.TestCase):
    def test_no_cycle(self):
        self.assertEqual(depmod.find_cycles({"B": ["A"], "A": []}), [])

    def test_two_cycle_canonical(self):
        self.assertEqual(depmod.find_cycles({"A": ["B"], "B": ["A"]}),
                         [["A", "B"]])

    def test_self_loop(self):
        self.assertEqual(depmod.find_cycles({"A": ["A"]}), [["A"]])

    def test_deterministic_across_insertion_orders(self):
        g1 = {"A": ["B"], "B": ["C"], "C": ["A"]}
        g2 = {"C": ["A"], "A": ["B"], "B": ["C"]}
        self.assertEqual(depmod.find_cycles(g1), depmod.find_cycles(g2))
        self.assertEqual(depmod.find_cycles(g1), [["A", "B", "C"]])

    def test_hostile_never_raises(self):
        self.assertEqual(depmod.find_cycles(None), [])
        self.assertEqual(depmod.find_cycles({"A": "nope"}), [])


class BreakCyclesTest(unittest.TestCase):
    def test_dag_order_prereqs_first(self):
        plan = depmod.break_cycles({"B": ["A"], "C": ["B"], "A": []})
        self.assertEqual(plan["order"], ["A", "B", "C"])
        self.assertEqual(plan["dropped"], [])

    def test_tie_break_drops_greatest_edge(self):
        plan = depmod.break_cycles({"A": ["B"], "B": ["C"], "C": ["A"]})
        self.assertEqual(plan["dropped"], [("C", "A")])
        self.assertEqual(sorted(plan["order"]), ["A", "B", "C"])

    def test_deterministic_across_insertion_orders(self):
        g1 = {"A": ["B"], "B": ["A"], "C": ["A"]}
        g2 = {"C": ["A"], "B": ["A"], "A": ["B"]}
        self.assertEqual(depmod.break_cycles(g1), depmod.break_cycles(g2))

    def test_result_is_acyclic(self):
        edges = {"A": ["B"], "B": ["C"], "C": ["A"], "D": ["C"]}
        plan = depmod.break_cycles(edges)
        pos = {n: i for i, n in enumerate(plan["order"])}
        kept = {(s, d) for s in edges for d in edges[s]} - set(plan["dropped"])
        for s, d in kept:
            self.assertLess(pos[d], pos[s])


class OrderNodesTest(unittest.TestCase):
    def test_legacy_no_data_fallback_keeps_input_order(self):
        self.assertEqual(depmod.order_nodes(["C", "A", "B"], {}),
                         ["C", "A", "B"])
        self.assertEqual(depmod.order_nodes(["C", "A", "B"], None),
                         ["C", "A", "B"])

    def test_cycle_still_orders_every_node(self):
        self.assertEqual(sorted(depmod.order_nodes(["B", "A"],
                         {"A": ["B"], "B": ["A"]})), ["A", "B"])

    def test_behavioral_effect_prereq_first(self):
        out = depmod.order_nodes(["Serve", "Read"], {"Serve": ["Read"]})
        self.assertEqual(out, ["Read", "Serve"])

    def test_hostile_never_raises(self):
        self.assertEqual(depmod.order_nodes(None, None), [])
        self.assertEqual(depmod.order_nodes(["A"], "nope"), ["A"])


class CallerEffectTest(unittest.TestCase):
    def test_cyclic_selection_keeps_input_order_deterministically(self):
        # Caller: select._prereqs_first drops depcycle's deterministic
        # edge, so the score order survives the cycle intact.
        concepts = [_scored("m:b", "b"), _scored("m:a", "a")]
        edges = [("m:b", "m:a", "calls"), ("m:a", "m:b", "calls")]
        first = [c.node_id for c in selmod._prereqs_first(concepts, edges)]
        self.assertEqual(first, ["m:b", "m:a"])
        flipped = [("m:a", "m:b", "calls"), ("m:b", "m:a", "calls")]
        again = [c.node_id for c in selmod._prereqs_first(concepts, flipped)]
        self.assertEqual(again, first)

    def test_dag_keeps_legacy_emit_order(self):
        concepts = [_scored("m:b", "b"), _scored("m:a", "a")]
        edges = [("m:b", "m:a", "calls")]
        out = [c.node_id for c in selmod._prereqs_first(concepts, edges)]
        self.assertEqual(out, ["m:a", "m:b"])

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{depmod.STATUS_ANCHOR}'",
                      depmod.section_html())
        e = depmod.tour_entry()
        self.assertEqual(e["id"], depmod.DEPCYCLE_ID)
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], depmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
