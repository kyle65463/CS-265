import unittest
from utils.inline.graph import form_call_graph


class TestFormCallGraph(unittest.TestCase):
    def test_empty_program(self):
        prog = {"functions": []}
        nodes, edges = form_call_graph(prog)
        self.assertEqual(nodes, {})
        self.assertEqual(edges, [])

    def test_single_function_no_calls(self):
        prog = {"functions": [{"name": "A", "instrs": []}]}
        nodes, edges = form_call_graph(prog)
        self.assertIn("A", nodes)
        self.assertEqual(nodes["A"]["edges"], [])
        self.assertEqual(edges, [])

    def test_single_function_multiple_calls(self):
        # A calls B, C, D
        prog = {
            "functions": [
                {
                    "name": "A",
                    "instrs": [
                        {"op": "call", "funcs": ["B"]},
                        {"op": "call", "funcs": ["C"]},
                        {"op": "call", "funcs": ["D"]},
                    ],
                },
                {"name": "B", "instrs": []},
                {"name": "C", "instrs": []},
                {"name": "D", "instrs": []},
            ]
        }
        nodes, edges = form_call_graph(prog)
        self.assertEqual(set(nodes["A"]["edges"]), {"B", "C", "D"})
        self.assertTrue(
            ("A", "B") in edges and ("A", "C") in edges and ("A", "D") in edges
        )

    def test_multiple_functions_no_calls(self):
        prog = {
            "functions": [
                {"name": "A", "instrs": []},
                {"name": "B", "instrs": []},
                {"name": "C", "instrs": []},
            ]
        }
        nodes, edges = form_call_graph(prog)
        self.assertEqual(len(nodes), 3)
        for n in nodes:
            self.assertEqual(nodes[n]["edges"], [])
        self.assertEqual(edges, [])

    def test_duplicate_calls(self):
        # A calls B twice
        prog = {
            "functions": [
                {
                    "name": "A",
                    "instrs": [
                        {"op": "call", "funcs": ["B"]},
                        {"op": "call", "funcs": ["B"]},
                    ],
                },
                {"name": "B", "instrs": []},
            ]
        }
        nodes, edges = form_call_graph(prog)
        self.assertEqual(nodes["A"]["edges"], ["B"])
        self.assertEqual(edges, [("A", "B")])

    def test_complex_calls(self):
        # A calls B, B calls C, C calls A and W
        # W calls X, forming a more complex structure
        prog = {
            "functions": [
                {"name": "A", "instrs": [{"op": "call", "funcs": ["B"]}]},
                {"name": "B", "instrs": [{"op": "call", "funcs": ["C"]}]},
                {
                    "name": "C",
                    "instrs": [
                        {"op": "call", "funcs": ["A"]},
                        {"op": "call", "funcs": ["W"]},
                    ],
                },
                {"name": "W", "instrs": [{"op": "call", "funcs": ["X"]}]},
                {"name": "X", "instrs": []},
            ]
        }
        nodes, edges = form_call_graph(prog)
        self.assertIn("A", nodes)
        self.assertCountEqual(nodes["A"]["edges"], ["B"])
        self.assertCountEqual(nodes["C"]["edges"], ["A", "W"])
        self.assertIn(("C", "W"), edges)
