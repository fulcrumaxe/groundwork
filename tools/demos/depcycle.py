"""Improvement demo: deterministic cycle-breaking (I-132).

Full behavior: circular lesson prerequisites order prerequisites-first with
the lexicographically greatest in-cycle edge dropped -- the same graph
orders the same way every run. The real caller is concept selection at
module creation; the terminal beats drive select_concepts on a cyclic
synthetic graph twice to prove determinism.
"""
from __future__ import annotations

SCENARIO = {
    "id": "depcycle",
    "kind": "improvement",
    "batch": 21,
    "item": "I-132",
    "title": "Deterministic cycle-breaking",
    "blurb": "Circular prerequisites break the same way every run -- order never flips.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Improvement I-132",
         "title": "Deterministic cycle-breaking",
         "subtitle": "Circular prerequisites freeze ordering -- unless the break is fixed."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-depcycle",
         "caption": "Status documents the breaker with a live cyclic demo.",
         "assert_js": "() => !!document.querySelector('#status-b21-depcycle') && "
                      "document.body.innerText.includes('dropped=')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: same cycle in, same order and drop out.",
         "commands": [
             ["python3", "-c",
              "from groundwork import depcycle as m; "
              "edges = {'Serve': ['Grade'], 'Grade': ['Read'], 'Read': ['Serve']}; "
              "print('cycles:', m.find_cycles(edges)); "
              "plan = m.break_cycles(edges); "
              "print('order:', plan['order'], '| dropped:', plan['dropped']); "
              "print('repeat:', m.break_cycles(edges) == plan); "
              "print('legacy:', m.order_nodes(['b', 'a'], {}))"],
         ]},
        {"type": "terminal", "duration": 10,
         "caption": "The real caller: concept selection orders the cycle -- twice, identically.",
         "commands": [
             ["python3", "-c",
              "from types import SimpleNamespace; "
              "from groundwork import select as s; "
              "nodes = {n: SimpleNamespace(name=n, kind='function', file='g.py', line=1, complexity=1) for n in 'ABC'}; "
              "g = SimpleNamespace(nodes=nodes, edges=[('A','B','x'),('B','C','x'),('C','A','x')], "
              "out_degree=lambda n: 1); "
              "runs = [[c.node_id for c in s.select_concepts(g, ['A','B','C'], keep=3)] "
              "for _ in range(2)]; "
              "print('run 1:', runs[0]); print('run 2:', runs[1]); "
              "print('deterministic:', runs[0] == runs[1])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "Same graph, same order.",
         "subtitle": "depcycle.py drops the greatest edge -- acyclic graphs keep legacy order."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Db-free item: the caller path is pure ordering, no fixture needed."""
    return {"seeded": False, "reason": "db-free"}
