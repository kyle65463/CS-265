import unittest
from utils.inline.optimal import (
    find_bridges,
    find_connected_components,
    compute_eccentricity,
    select_partition_edge,
    remove_edge,
    inline_edge,
    build_inlining_tree,
    InliningTreeLeaf,
    InliningTreeBinaryNode,
)


class TestFindBridges(unittest.TestCase):
    def test_no_edges(self):
        nodes = {"A": {"edges": []}}
        edges = []
        bridges = find_bridges(nodes, edges)
        self.assertEqual(bridges, [])

    def test_single_edge_graph(self):
        # A->B only
        nodes = {"A": {"edges": ["B"]}, "B": {"edges": []}}
        edges = [("A", "B")]
        # Single edge is a bridge in undirected sense
        bridges = find_bridges(nodes, edges)
        self.assertEqual(bridges, [("A", "B")])

    def test_line_graph_all_bridges(self):
        # A->B->C->D
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C"]},
            "C": {"edges": ["D"]},
            "D": {"edges": []},
        }
        edges = [("A", "B"), ("B", "C"), ("C", "D")]
        # All edges in a linear chain are bridges
        bridges = find_bridges(nodes, edges)
        self.assertCountEqual(bridges, edges)

    def test_cycle_graph_no_bridges(self):
        # A->B->C->A (cycle)
        nodes = {"A": {"edges": ["B"]}, "B": {"edges": ["C"]}, "C": {"edges": ["A"]}}
        edges = [("A", "B"), ("B", "C"), ("C", "A")]
        # No edges are bridges in a pure cycle
        bridges = find_bridges(nodes, edges)
        self.assertEqual(bridges, [])

    def test_cycle_with_spoke_some_bridges(self):
        nodes = {
            "A": {"edges": ["B", "D"]},
            "B": {"edges": ["C"]},
            "C": {"edges": ["A"]},
            "D": {"edges": []},
        }
        edges = [("A", "B"), ("B", "C"), ("C", "A"), ("A", "D")]
        bridges = find_bridges(nodes, edges)
        self.assertCountEqual(bridges, [("A", "D")])

    def test_cycle_plus_chain_partial_bridges(self):
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C", "D"]},
            "C": {"edges": []},
            "D": {"edges": ["E"]},
            "E": {"edges": ["B"]},
        }
        edges = [("A", "B"), ("B", "C"), ("B", "D"), ("D", "E"), ("E", "B")]
        bridges = find_bridges(nodes, edges)
        self.assertCountEqual(bridges, [("A", "B"), ("B", "C")])

    def test_two_components_connected_by_a_bridge(self):
        nodes = {
            "X": {"edges": ["Y"]},
            "Y": {"edges": ["Z"]},
            "Z": {"edges": ["P"]},
            "P": {"edges": ["Q"]},
            "Q": {"edges": []},
        }
        edges = [("X", "Y"), ("Y", "Z"), ("Z", "P"), ("P", "Q")]
        bridges = find_bridges(nodes, edges)
        self.assertCountEqual(bridges, edges)

    def test_mixed_scenario_partial_bridges(self):
        nodes = {
            "F": {"edges": ["G"]},
            "G": {"edges": ["H"]},
            "H": {"edges": ["F", "I"]},
            "I": {"edges": ["J"]},
            "J": {"edges": []},
        }
        edges = [("F", "G"), ("G", "H"), ("H", "F"), ("H", "I"), ("I", "J")]
        bridges = find_bridges(nodes, edges)
        self.assertCountEqual(bridges, [("H", "I"), ("I", "J")])


class TestFindConnectedComponents(unittest.TestCase):
    def test_single_node_no_edges(self):
        nodes = {"A": {"edges": []}}
        edges = []
        comps = find_connected_components(nodes, edges)
        self.assertEqual(len(comps), 1)
        self.assertIn("A", comps[0][0])

    def test_multiple_isolated_nodes(self):
        nodes = {"A": {"edges": []}, "B": {"edges": []}, "C": {"edges": []}}
        edges = []
        comps = find_connected_components(nodes, edges)
        # Each node is its own component
        self.assertEqual(len(comps), 3)

    def test_line_graph_single_component(self):
        # A->B->C
        nodes = {"A": {"edges": ["B"]}, "B": {"edges": ["C"]}, "C": {"edges": []}}
        edges = [("A", "B"), ("B", "C")]
        comps = find_connected_components(nodes, edges)
        self.assertEqual(len(comps), 1)
        self.assertCountEqual(comps[0][0].keys(), ["A", "B", "C"])

    def test_multiple_components(self):
        # A->B and C->D separate
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": []},
            "C": {"edges": ["D"]},
            "D": {"edges": []},
        }
        edges = [("A", "B"), ("C", "D")]
        comps = find_connected_components(nodes, edges)
        self.assertEqual(len(comps), 2)

    def test_component_with_cycle(self):
        # A->B->C->A cycle and D isolated
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C"]},
            "C": {"edges": ["A"]},
            "D": {"edges": []},
        }
        edges = [("A", "B"), ("B", "C"), ("C", "A")]
        comps = find_connected_components(nodes, edges)
        # One component with A,B,C and one with D
        self.assertEqual(len(comps), 2)


class TestComputeEccentricity(unittest.TestCase):
    def test_isolated_node(self):
        nodes = {"A": {"edges": []}}
        edges = []
        self.assertEqual(compute_eccentricity(nodes, edges, "A"), 0)

    def test_line_graph(self):
        # A->B->C->D
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C"]},
            "C": {"edges": ["D"]},
            "D": {"edges": []},
        }
        edges = [("A", "B"), ("B", "C"), ("C", "D")]

        self.assertEqual(compute_eccentricity(nodes, edges, "A"), 3)
        self.assertEqual(compute_eccentricity(nodes, edges, "B"), 2)
        self.assertEqual(compute_eccentricity(nodes, edges, "C"), 2)
        self.assertEqual(compute_eccentricity(nodes, edges, "D"), 3)

    def test_cycle_graph(self):
        # A->B->C->A
        nodes = {"A": {"edges": ["B"]}, "B": {"edges": ["C"]}, "C": {"edges": ["A"]}}
        edges = [("A", "B"), ("B", "C"), ("C", "A")]
        for n in ["A", "B", "C"]:
            self.assertEqual(compute_eccentricity(nodes, edges, n), 1)

    def test_star_graph(self):
        # C->A, C->B, C->D
        nodes = {
            "A": {"edges": []},
            "B": {"edges": []},
            "C": {"edges": ["A", "B", "D"]},
            "D": {"edges": []},
        }
        edges = [("C", "A"), ("C", "B"), ("C", "D")]
        self.assertEqual(compute_eccentricity(nodes, edges, "C"), 1)
        for leaf in ["A", "B", "D"]:
            self.assertEqual(compute_eccentricity(nodes, edges, leaf), 2)

    def test_isolated_multiple_nodes(self):
        # A,B,C all isolated
        nodes = {"A": {"edges": []}, "B": {"edges": []}, "C": {"edges": []}}
        edges = []
        for n in nodes:
            self.assertEqual(compute_eccentricity(nodes, edges, n), 0)

    def test_partial_reachability(self):
        #  A->B->C and D->E
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C"]},
            "C": {"edges": []},
            "D": {"edges": ["E"]},
            "E": {"edges": []},
        }
        edges = [("A", "B"), ("B", "C"), ("D", "E")]
        self.assertEqual(compute_eccentricity(nodes, edges, "A"), 2)
        self.assertEqual(compute_eccentricity(nodes, edges, "B"), 1)
        self.assertEqual(compute_eccentricity(nodes, edges, "C"), 2)
        self.assertEqual(compute_eccentricity(nodes, edges, "D"), 1)
        self.assertEqual(compute_eccentricity(nodes, edges, "E"), 1)

    def test_complex_graph_undirected(self):
        # A->B, B->C, C->A (cycle)
        # A->D
        # E->A
        nodes = {
            "A": {"edges": ["B", "D"]},
            "B": {"edges": ["C"]},
            "C": {"edges": ["A"]},
            "D": {"edges": []},
            "E": {"edges": ["A"]},
        }
        edges = [("A", "B"), ("A", "D"), ("B", "C"), ("C", "A"), ("E", "A")]
        self.assertEqual(compute_eccentricity(nodes, edges, "A"), 1)
        self.assertEqual(compute_eccentricity(nodes, edges, "B"), 2)
        self.assertEqual(compute_eccentricity(nodes, edges, "C"), 2)
        self.assertEqual(compute_eccentricity(nodes, edges, "D"), 2)
        self.assertEqual(compute_eccentricity(nodes, edges, "E"), 2)


class TestSelectPartitionEdge(unittest.TestCase):
    def test_single_bridge(self):
        # Simple linear graph: A->B->C
        nodes = {"A": {"edges": ["B"]}, "B": {"edges": ["C"]}, "C": {"edges": []}}
        edges = [("A", "B"), ("B", "C")]
        # Both (A,B) and (B,C) are bridges. B has ecc=1, A and C have ecc=2
        # Least ecc node adjacent to a bridge is B (ecc=1)
        # Among bridges adjacent to B, (A,B) and (B,C), select the first in sorted order
        result = select_partition_edge(nodes, edges)
        self.assertEqual(result, ("A", "B"))

    def test_cycle_with_bridge(self):
        # Cycle A->B->C->A and a bridge A->D
        nodes = {
            "A": {"edges": ["B", "D"]},
            "B": {"edges": ["C"]},
            "C": {"edges": ["A"]},
            "D": {"edges": []},
        }
        edges = [("A", "B"), ("B", "C"), ("C", "A"), ("A", "D")]
        result = select_partition_edge(nodes, edges)
        self.assertEqual(result, ("A", "D"))

    def test_cycle_with_multiple_bridges(self):
        # Cycle A->B->C->A with bridges C->D and C->E
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C"]},
            "C": {"edges": ["A", "D", "E"]},
            "D": {"edges": []},
            "E": {"edges": []},
        }
        edges = [("A", "B"), ("B", "C"), ("C", "A"), ("C", "D"), ("C", "E")]
        # Bridges: (C,D), (C,E)
        # Eccentricities:
        # A, B, C: part of a cycle, ecc=2 (A can reach D/E via C)
        # D and E: ecc=3 (D can reach E via C, A, B or similar)
        # So select bridge adjacent to C (ecc=2) or D/E (ecc=3). C has lower ecc.
        # Among bridges (C,D) and (C,E), select the first in sorted order: (C,D)
        result = select_partition_edge(nodes, edges)
        self.assertEqual(result, ("C", "D"))

    def test_complex_graph_with_multiple_cycles_and_bridges(self):
        # Graph Structure:
        # Cycle A->B->C->A
        # Cycle C->D->E->C
        # Bridge C->F
        # F->G->F (cycle)
        # Bridge F->H
        # H->I->J
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C"]},
            "C": {"edges": ["A", "D", "F"]},
            "D": {"edges": ["E"]},
            "E": {"edges": ["C"]},
            "F": {"edges": ["G", "H"]},
            "G": {"edges": ["F"]},
            "H": {"edges": ["I"]},
            "I": {"edges": ["J"]},
            "J": {"edges": []},
        }
        edges = [
            ("A", "B"),
            ("B", "C"),
            ("C", "A"),
            ("C", "D"),
            ("D", "E"),
            ("E", "C"),
            ("C", "F"),
            ("F", "G"),
            ("G", "F"),
            ("F", "H"),
            ("H", "I"),
            ("I", "J"),
        ]
        result = select_partition_edge(nodes, edges)
        self.assertEqual(result, ("C", "F"))

    def test_no_bridges_select_high_out_degree_and_least_in_degree(self):
        # Complete graph: A->B, A->C, B->A, B->C, C->A, C->B
        # No bridges
        nodes = {
            "A": {"edges": ["B", "C"]},
            "B": {"edges": ["A", "C"]},
            "C": {"edges": ["A", "B"]},
        }
        edges = [("A", "B"), ("A", "C"), ("B", "A"), ("B", "C"), ("C", "A"), ("C", "B")]
        result = select_partition_edge(nodes, edges)
        self.assertEqual(result, ("A", "B"))

    def test_no_bridges_multiple_high_out_degree_nodes(self):
        # Graph:
        # A->B, A->C
        # B->A, B->C
        # C->A, C->B
        # D->E, D->F
        # E->D, E->F
        # F->D, F->E
        # No bridges
        nodes = {
            "A": {"edges": ["B", "C"]},
            "B": {"edges": ["A", "C"]},
            "C": {"edges": ["A", "B"]},
            "D": {"edges": ["E", "F"]},
            "E": {"edges": ["D", "F"]},
            "F": {"edges": ["D", "E"]},
        }
        edges = [
            ("A", "B"),
            ("A", "C"),
            ("B", "A"),
            ("B", "C"),
            ("C", "A"),
            ("C", "B"),
            ("D", "E"),
            ("D", "F"),
            ("E", "D"),
            ("E", "F"),
            ("F", "D"),
            ("F", "E"),
        ]
        result = select_partition_edge(nodes, edges)
        self.assertEqual(result, ("A", "B"))

    def test_multiple_bridges_same_ecc(self):
        # Graph:
        # A->B, B->C, C->D
        # C->E, E->F, F->C
        # D->G, G->H
        # H->I, I->J
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C"]},
            "C": {"edges": ["D", "E"]},
            "D": {"edges": ["G"]},
            "E": {"edges": ["F"]},
            "F": {"edges": ["C"]},
            "G": {"edges": ["H"]},
            "H": {"edges": ["I"]},
            "I": {"edges": ["J"]},
            "J": {"edges": []},
        }
        edges = [
            ("A", "B"),
            ("B", "C"),
            ("C", "D"),
            ("C", "E"),
            ("E", "F"),
            ("F", "C"),
            ("D", "G"),
            ("G", "H"),
            ("H", "I"),
            ("I", "J"),
        ]
        result = select_partition_edge(nodes, edges)
        self.assertEqual(result, ("C", "D"))

    def test_bridge_adjacent_to_least_ecc_node_with_multiple_options(self):
        # Graph:
        # A->B, B->C, C->D, D->E
        # B->F, F->G, G->B (cycle)
        # C->H
        # H->I, I->J
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C", "F"]},
            "C": {"edges": ["D", "H"]},
            "D": {"edges": ["E"]},
            "E": {"edges": []},
            "F": {"edges": ["G"]},
            "G": {"edges": ["B"]},
            "H": {"edges": ["I"]},
            "I": {"edges": ["J"]},
            "J": {"edges": []},
        }
        edges = [
            ("A", "B"),
            ("B", "C"),
            ("C", "D"),
            ("D", "E"),
            ("B", "F"),
            ("F", "G"),
            ("G", "B"),
            ("C", "H"),
            ("H", "I"),
            ("I", "J"),
        ]
        result = select_partition_edge(nodes, edges)
        self.assertEqual(result, ("B", "C"))

    def test_no_bridges_select_from_high_out_degree_least_in_degree(self):
        # Complete graph with additional edges forming multiple cycles, no bridges
        # A->B, A->C, A->D
        # B->A, B->C, B->D
        # C->A, C->B, C->D
        # D->A, D->B, D->C
        nodes = {
            "A": {"edges": ["B", "C", "D"]},
            "B": {"edges": ["A", "C", "D"]},
            "C": {"edges": ["A", "B", "D"]},
            "D": {"edges": ["A", "B", "C"]},
        }
        edges = [
            ("A", "B"),
            ("A", "C"),
            ("A", "D"),
            ("B", "A"),
            ("B", "C"),
            ("B", "D"),
            ("C", "A"),
            ("C", "B"),
            ("C", "D"),
            ("D", "A"),
            ("D", "B"),
            ("D", "C"),
        ]
        result = select_partition_edge(nodes, edges)
        self.assertEqual(result, ("A", "B"))

    def test_bridge_adjacent_to_multiple_least_ecc_nodes(self):
        # Graph:
        # A->B, B->C, C->A (cycle)
        # C->D, D->E, E->C (cycle)
        # C->F, F->G, G->C (cycle)
        # D->H
        # H->I
        # I->J
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C"]},
            "C": {"edges": ["A", "D", "F"]},
            "D": {"edges": ["E", "H"]},
            "E": {"edges": ["C"]},
            "F": {"edges": ["G"]},
            "G": {"edges": ["C"]},
            "H": {"edges": ["I"]},
            "I": {"edges": ["J"]},
            "J": {"edges": []},
        }
        edges = [
            ("A", "B"),
            ("B", "C"),
            ("C", "A"),
            ("C", "D"),
            ("D", "E"),
            ("E", "C"),
            ("C", "F"),
            ("F", "G"),
            ("G", "C"),
            ("D", "H"),
            ("H", "I"),
            ("I", "J"),
        ]
        result = select_partition_edge(nodes, edges)
        self.assertEqual(result, ("D", "H"))

    def test_bridge_selection_with_same_ecc_nodes(self):
        # Graph:
        # A->B, B->C, C->A (cycle)
        # B->D, D->E, E->B (cycle)
        # B->F
        # F->G, G->B (cycle)
        # G->H, H->I, I->J
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C", "D", "F"]},
            "C": {"edges": ["A"]},
            "D": {"edges": ["E"]},
            "E": {"edges": ["B"]},
            "F": {"edges": ["G"]},
            "G": {"edges": ["B", "H"]},
            "H": {"edges": ["I"]},
            "I": {"edges": ["J"]},
            "J": {"edges": []},
        }
        edges = [
            ("A", "B"),
            ("B", "C"),
            ("C", "A"),
            ("B", "D"),
            ("D", "E"),
            ("E", "B"),
            ("B", "F"),
            ("F", "G"),
            ("G", "B"),
            ("G", "H"),
            ("H", "I"),
            ("I", "J"),
        ]
        result = select_partition_edge(nodes, edges)
        self.assertEqual(result, ("G", "H"))

    def test_bridge_with_multiple_low_ecc_nodes(self):
        # Graph:
        # A->B, B->C, C->D, D->E
        # B->F, F->G, G->B (cycle)
        # D->H, H->I, I->J, J->D (cycle)
        # E->K
        # K->L
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C", "F"]},
            "C": {"edges": ["D"]},
            "D": {"edges": ["E", "H"]},
            "E": {"edges": ["K"]},
            "F": {"edges": ["G"]},
            "G": {"edges": ["B"]},
            "H": {"edges": ["I"]},
            "I": {"edges": ["J"]},
            "J": {"edges": ["D"]},
            "K": {"edges": ["L"]},
            "L": {"edges": []},
        }
        edges = [
            ("A", "B"),
            ("B", "C"),
            ("C", "D"),
            ("D", "E"),
            ("D", "H"),
            ("B", "F"),
            ("F", "G"),
            ("G", "B"),
            ("H", "I"),
            ("I", "J"),
            ("J", "D"),
            ("E", "K"),
            ("K", "L"),
        ]
        result = select_partition_edge(nodes, edges)
        self.assertEqual(result, ("C", "D"))


class TestRemoveEdge(unittest.TestCase):
    def test_remove_existing_edge(self):
        nodes = {"A": {"edges": ["B"]}, "B": {"edges": []}}
        edges = [("A", "B")]
        new_nodes, new_edges = remove_edge(nodes, edges, ("A", "B"))
        self.assertEqual(new_nodes["A"]["edges"], [])
        self.assertEqual(new_edges, [])

    def test_remove_non_existing_edge(self):
        nodes = {"A": {"edges": ["B"]}, "B": {"edges": []}}
        edges = [("A", "B")]
        new_nodes, new_edges = remove_edge(nodes, edges, ("A", "C"))
        # Should remain unchanged
        self.assertEqual(new_nodes["A"]["edges"], ["B"])
        self.assertEqual(new_edges, [("A", "B")])

    def test_remove_edge_from_node_with_multiple_edges(self):
        # A->B, A->C, A->D
        nodes = {
            "A": {"edges": ["B", "C", "D"]},
            "B": {"edges": []},
            "C": {"edges": []},
            "D": {"edges": []},
        }
        edges = [("A", "B"), ("A", "C"), ("A", "D")]
        new_nodes, new_edges = remove_edge(nodes, edges, ("A", "C"))
        self.assertEqual(set(new_nodes["A"]["edges"]), {"B", "D"})
        self.assertCountEqual(new_edges, [("A", "B"), ("A", "D")])

    def test_remove_edge_in_cyclic_graph(self):
        # Graph: A->B, B->C, C->A, C->D
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C"]},
            "C": {"edges": ["A", "D"]},
            "D": {"edges": []},
        }
        edges = [("A", "B"), ("B", "C"), ("C", "A"), ("C", "D")]
        new_nodes, new_edges = remove_edge(nodes, edges, ("C", "D"))
        self.assertEqual(new_nodes["C"]["edges"], ["A"])
        self.assertCountEqual(new_edges, [("A", "B"), ("B", "C"), ("C", "A")])


class TestInlineEdge(unittest.TestCase):
    def test_inline_simple_case(self):
        nodes = {"A": {"edges": ["B"]}, "B": {"edges": ["C"]}, "C": {"edges": []}}
        edges = [("A", "B"), ("B", "C")]
        new_nodes, new_edges = inline_edge(nodes, edges, ("A", "B"))
        self.assertEqual(
            new_nodes,
            {"A": {"edges": ["C"]}, "C": {"edges": []}},
        )
        self.assertCountEqual(new_edges, [("A", "C")])

    def test_inline_with_multiple_callers(self):
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C"]},
            "C": {"edges": []},
            "D": {"edges": ["B"]},
        }
        edges = [("A", "B"), ("B", "C"), ("D", "B")]
        new_nodes, new_edges = inline_edge(nodes, edges, ("A", "B"))
        self.assertEqual(
            new_nodes,
            {
                "A_B": {"edges": ["C"]},
                "B": {"edges": ["C"]},
                "C": {"edges": []},
                "D": {"edges": ["B"]},
            },
        )
        self.assertCountEqual(new_edges, [("A_B", "C"), ("D", "B"), ("B", "C")])

    def test_inline_with_multiple_callers2(self):
        nodes = {
            "X": {"edges": ["A"]},
            "A": {"edges": ["B"]},
            "B": {"edges": ["C"]},
            "C": {"edges": []},
            "D": {"edges": ["B"]},
        }
        edges = [("X", "A"), ("A", "B"), ("B", "C"), ("D", "B")]
        new_nodes, new_edges = inline_edge(nodes, edges, ("A", "B"))
        self.assertEqual(
            new_nodes,
            {
                "A_B": {"edges": ["C"]},
                "B": {"edges": ["C"]},
                "C": {"edges": []},
                "D": {"edges": ["B"]},
                "X": {"edges": ["A_B"]},
            },
        )
        self.assertCountEqual(
            new_edges, [("X", "A_B"), ("A_B", "C"), ("D", "B"), ("B", "C")]
        )

    def test_inline_self_loop(self):
        nodes = {"A": {"edges": ["A"]}}
        edges = [("A", "A")]
        with self.assertRaises(ValueError):
            inline_edge(nodes, edges, ("A", "A"))

    def test_inline_edge_not_present(self):
        nodes = {"A": {"edges": ["B"]}, "B": {"edges": ["C"]}, "C": {"edges": []}}
        edges = [("A", "B"), ("B", "C")]
        new_nodes, new_edges = inline_edge(nodes, edges, ("A", "C"))
        self.assertEqual(new_nodes, nodes)
        self.assertEqual(new_edges, edges)

    def test_inline_with_no_outgoing_edges(self):
        nodes = {"A": {"edges": ["B"]}, "B": {"edges": []}}
        edges = [("A", "B")]
        new_nodes, new_edges = inline_edge(nodes, edges, ("A", "B"))
        self.assertEqual(
            new_nodes,
            {"A": {"edges": []}},
        )
        self.assertEqual(new_edges, [])

    def test_inline_with_multiple_outgoing_edges(self):
        nodes = {
            "A": {"edges": ["B"]},
            "B": {"edges": ["C", "D", "E"]},
            "C": {"edges": []},
            "D": {"edges": []},
            "E": {"edges": []},
        }
        edges = [("A", "B"), ("B", "C"), ("B", "D"), ("B", "E")]
        new_nodes, new_edges = inline_edge(nodes, edges, ("A", "B"))
        self.assertCountEqual(
            new_nodes["A"]["edges"],
            ["C", "D", "E"],
        )
        self.assertNotIn("B", new_nodes)
        self.assertEqual(new_nodes["C"]["edges"], [])
        self.assertEqual(new_nodes["D"]["edges"], [])
        self.assertEqual(new_nodes["E"]["edges"], [])
        self.assertCountEqual(new_edges, [("A", "C"), ("A", "D"), ("A", "E")])


class TestBuildInliningTree(unittest.TestCase):
    def test_empty_graph(self):
        nodes = {}
        edges = []
        tree = build_inlining_tree(nodes, edges)
        self.assertIsInstance(tree, InliningTreeLeaf)
        self.assertEqual(tree.edges, [])

    def test_single_edge(self):
        # A->B
        nodes = {"A": {"edges": ["B"]}, "B": {"edges": []}}
        edges = [("A", "B")]
        tree = build_inlining_tree(nodes, edges)
        self.assertIsInstance(tree, InliningTreeBinaryNode)
        self.assertEqual(tree.partition_edge, ("A", "B"))


if __name__ == "__main__":
    unittest.main()
