import copy
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import ast
from pathlib import Path
import csv

from utils.inline.graph import form_call_graph


@dataclass
class InliningTreeNode:
    call_graph: Dict
    edges: List[Tuple[str, str]]

    def is_leaf(self) -> bool:
        return len(self.edges) == 0

    def to_dict(self) -> Dict:
        return {
            "type": self.__class__.__name__,
            "call_graph": self.call_graph,
            "edges": self.edges,
        }


class InliningTreeLeaf(InliningTreeNode):
    pass


class InliningTreeBinaryNode(InliningTreeNode):
    def __init__(
        self,
        call_graph: Dict,
        edges: List[Tuple[str, str]],
        partition_edge: Tuple[str, str],
        not_inlined: InliningTreeNode,
        inlined: InliningTreeNode,
    ):
        super().__init__(call_graph, edges)
        self.partition_edge = partition_edge
        self.not_inlined = not_inlined
        self.inlined = inlined

    def to_dict(self) -> Dict:
        result = super().to_dict()
        result.update(
            {
                "partition_edge": self.partition_edge,
                "not_inlined": self.not_inlined.to_dict(),
                "inlined": self.inlined.to_dict(),
            }
        )
        return result


class InliningTreeComponentsNode(InliningTreeNode):
    def __init__(
        self,
        call_graph: Dict,
        edges: List[Tuple[str, str]],
        components: List[InliningTreeNode],
    ):
        super().__init__(call_graph, edges)
        self.components = components

    def to_dict(self) -> Dict:
        result = super().to_dict()
        result["components"] = [comp.to_dict() for comp in self.components]
        return result


def find_bridges(nodes: Dict, edges: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Find bridges in the call graph by viewing it as an undirected graph."""
    undirected_adj = defaultdict(set)
    for u, v in edges:
        undirected_adj[u].add(v)
        undirected_adj[v].add(u)

    disc = {}
    low = {}
    time = [0]
    bridges = []

    def dfs(u: str, parent: Optional[str] = None):
        disc[u] = low[u] = time[0]
        time[0] += 1

        for v in undirected_adj[u]:
            if v not in disc:
                dfs(v, u)
                low[u] = min(low[u], low[v])
                if low[v] > disc[u]:
                    # Add bridge if it matches direction in original edges
                    if (u, v) in edges:
                        bridges.append((u, v))
                    elif (v, u) in edges:
                        bridges.append((v, u))
            elif v != parent:
                low[u] = min(low[u], disc[v])

    for node in nodes:
        if node not in disc:
            dfs(node)

    return bridges


def find_connected_components(nodes, edges):
    visited = set()
    components = []

    # Compute incoming edges
    incoming = set(v for _, v in edges)
    root_nodes = set(nodes.keys()) - incoming
    if not root_nodes:
        # If no root nodes, use all nodes as potential starts
        root_nodes = set(nodes.keys())

    # BFS or DFS helper
    def dfs(start, visited):
        stack = [start]
        component = set()
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                component.add(node)
                # For connected components, treat graph undirected:
                neighbors = set(nodes[node]["edges"]) | {
                    u for (u, v) in edges if v == node
                }  # add incoming as neighbors
                for neigh in neighbors:
                    if neigh not in visited:
                        stack.append(neigh)
        return component

    # First pass: from root nodes
    for root in root_nodes:
        if root not in visited:
            comp = dfs(root, visited)
            components.append(
                (
                    {n: nodes[n] for n in comp},
                    [(u, v) for (u, v) in edges if u in comp and v in comp],
                )
            )

    # Second pass: from any remaining unvisited nodes
    for node in nodes:
        if node not in visited:
            comp = dfs(node, visited)
            components.append(
                (
                    {n: nodes[n] for n in comp},
                    [(u, v) for (u, v) in edges if u in comp and v in comp],
                )
            )

    return components


def compute_eccentricity(nodes: Dict, edges: List[Tuple[str, str]], start: str) -> int:
    # Build undirected adjacency
    undirected_adj = {n: set() for n in nodes}
    for u, v in edges:
        undirected_adj[u].add(v)
        undirected_adj[v].add(u)

    from collections import deque

    distances = {n: float("inf") for n in nodes}
    distances[start] = 0
    queue = deque([start])

    while queue:
        curr = queue.popleft()
        for neigh in undirected_adj[curr]:
            if distances[neigh] == float("inf"):
                distances[neigh] = distances[curr] + 1
                queue.append(neigh)

    # Filter out unreachable nodes (distance=inf)
    reachable_distances = [d for d in distances.values() if d != float("inf")]
    return max(reachable_distances) if reachable_distances else 0


def select_partition_edge(
    nodes: Dict[str, Dict], edges: List[Tuple[str, str]]
) -> Optional[Tuple[str, str]]:
    """
    Select an edge to partition the graph based on the following heuristic:
    1. If bridges exist, select the bridge adjacent to the node with the least eccentricity.
    2. If multiple bridges qualify, select the one with the lexicographically smallest edge.
    3. If no bridges exist, select the edge adjacent to the node with the highest out-degree.
       Tie-break by lexicographical order.
    """
    bridges = find_bridges(nodes, edges)

    if bridges:
        bridge_ecc = []
        for u, v in bridges:
            ecc_u = compute_eccentricity(nodes, edges, u)
            ecc_v = compute_eccentricity(nodes, edges, v)
            min_ecc = min(ecc_u, ecc_v)
            bridge_ecc.append((min_ecc, u, v))

        # Find the minimum eccentricity among all bridges
        min_ecc_overall = min(be[0] for be in bridge_ecc)

        # Filter bridges that are adjacent to nodes with this minimum eccentricity
        candidate_bridges = [
            (u, v) for (ecc, u, v) in bridge_ecc if ecc == min_ecc_overall
        ]

        # Sort the candidate bridges lexicographically and select the first one
        selected_bridge = sorted(candidate_bridges)[0]
        return selected_bridge
    else:
        # No bridges. Select edge adjacent to node with highest out-degree.
        # Compute out-degrees
        out_degrees = {n: len(nodes[n]["edges"]) for n in nodes}
        max_out_degree = max(out_degrees.values())

        # Get all nodes with the maximum out-degree, sorted lexicographically
        candidate_nodes = sorted(
            [n for n, deg in out_degrees.items() if deg == max_out_degree]
        )

        # From the first node, select the lex smallest target
        first_node = candidate_nodes[0]
        if not nodes[first_node]["edges"]:
            return None  # No edges to select
        selected_target = sorted(nodes[first_node]["edges"])[0]
        return (first_node, selected_target)


def remove_edge(
    nodes: Dict, edges: List[Tuple[str, str]], edge: Tuple[str, str]
) -> Tuple[Dict, List[Tuple[str, str]]]:
    src, dst = edge
    new_nodes = copy.deepcopy(nodes)
    new_edges = [e for e in edges if e != edge]

    # Remove dst from src's edges
    if dst in new_nodes[src]["edges"]:
        new_nodes[src]["edges"].remove(dst)

    return new_nodes, new_edges


def inline_edge(
    nodes: Dict[str, Dict], edges: List[Tuple[str, str]], edge: Tuple[str, str]
) -> Tuple[Dict[str, Dict], List[Tuple[str, str]]]:
    """Inline an edge by merging the destination node into the source node.

    Args:
        nodes: A dictionary where keys are node names and values are dictionaries with an "edges" key listing outgoing edges.
        edges: A list of tuples representing directed edges.
        edge: A tuple representing the edge to inline (src, dst).

    Returns:
        Updated nodes and edges after inlining the specified edge.
    """
    src, dst = edge

    # Verify that the edge exists in the graph
    if edge not in edges:
        return copy.deepcopy(nodes), edges[:]  # Return unchanged

    # Detect recursive calls (self-loops)
    if src == dst:
        raise ValueError(f"Cannot inline a self-loop: {edge}")

    # Make deep copies of nodes and edges
    new_nodes = copy.deepcopy(nodes)
    new_edges = []

    # Find incoming edges to dst
    incoming_edges = [u for u, v in edges if v == dst]

    if len(incoming_edges) > 1:
        # Clone the destination (dst) for the specific caller (src)
        clone_name = f"{src}_{dst}"  # Use deterministic clone naming
        new_nodes[clone_name] = {"edges": new_nodes[dst]["edges"][:]}  # Copy edges
        for node in new_nodes:
            for i, v in enumerate(new_nodes[node]["edges"]):
                if v == src:
                    new_nodes[node]["edges"][i] = clone_name
        del new_nodes[src]

        for u, v in edges:
            if u == src and v == dst:
                pass
            elif v == src:
                new_edges.append((u, clone_name))
            else:
                if u == dst:
                    new_edges.append((clone_name, v))
                new_edges.append((u, v))
    else:
        # Merge the destination (dst) into the source (src)
        dst_edges = [
            e for e in new_nodes[dst]["edges"] if e != dst
        ]  # Exclude self-loops
        new_nodes[src]["edges"] = list(
            set(new_nodes[src]["edges"] + dst_edges)
            - {dst}  # Remove dst from src's edges
        )

        for u, v in edges:
            if (u, v) == edge:
                continue  # Remove the inlined edge
            if u == dst:
                u = src  # Redirect edges from dst to src
            new_edges.append((u, v))

        # Remove the destination node
        del new_nodes[dst]

    # Deduplicate and remove self-loops
    new_edges = list(set(new_edges))
    new_edges = [(u, v) for (u, v) in new_edges if u != v]

    return new_nodes, new_edges


def build_inlining_tree(nodes: Dict, edges: List[Tuple[str, str]]) -> InliningTreeNode:
    """Main entry point for building the inlining tree."""
    if not edges:
        return InliningTreeLeaf(nodes, edges)

    components = find_connected_components(nodes, edges)
    if len(components) > 1:
        # Multiple components: build a ComponentsNode
        component_trees = []
        for component_nodes, component_edges in components:
            subtree = build_inlining_tree(component_nodes, component_edges)
            component_trees.append(subtree)
        return InliningTreeComponentsNode(nodes, edges, component_trees)

    # Single component: find partition edge
    partition_edge = select_partition_edge(nodes, edges)
    if not partition_edge:
        return InliningTreeLeaf(nodes, edges)

    # Not inlined subtree
    not_inlined_nodes, not_inlined_edges = remove_edge(nodes, edges, partition_edge)
    not_inlined_tree = build_inlining_tree(not_inlined_nodes, not_inlined_edges)

    # Inlined subtree
    inlined_nodes, inlined_edges = inline_edge(nodes, edges, partition_edge)
    inlined_tree = build_inlining_tree(inlined_nodes, inlined_edges)

    return InliningTreeBinaryNode(
        nodes, edges, partition_edge, not_inlined_tree, inlined_tree
    )


def print_inlining_tree(
    node: InliningTreeNode, prefix: str = "", is_last: bool = True
) -> None:
    """Utility function to print the inlining tree."""
    if isinstance(node, InliningTreeBinaryNode):
        print(
            f"{prefix}{'└── ' if is_last else '├── '}Binary Node (Edge {node.partition_edge[0]}–{node.partition_edge[1]})"
        )
        new_prefix = prefix + ("    " if is_last else "│   ")
        # Print not inlined subtree
        print(f"{new_prefix}├── Not Inlined:")
        print_inlining_tree(node.not_inlined, new_prefix + "│   ", False)
        # Print inlined subtree
        print(f"{new_prefix}└── Inlined:")
        print_inlining_tree(node.inlined, new_prefix + "    ", True)

    elif isinstance(node, InliningTreeComponentsNode):
        print(f"{prefix}{'└── ' if is_last else '├── '}Components Node")
        new_prefix = prefix + ("    " if is_last else "│   ")
        for i, component in enumerate(node.components):
            print_inlining_tree(component, new_prefix, i == len(node.components) - 1)

    elif isinstance(node, InliningTreeLeaf):
        edges_str = (
            ", ".join(f"{u}–{v}" for u, v in node.edges) if node.edges else "no edges"
        )
        print(f"{prefix}{'└── ' if is_last else '├── '}Leaf ({edges_str})")


def collect_all_configurations_iterative(
    root: InliningTreeNode,
) -> List[Dict]:
    """
    Traverse the inlining tree iteratively and collect all possible inlining configurations.
    Each configuration includes a decision for every edge in the original graph.
    Duplicate configurations are eliminated.
    """
    # Get all edges from the root node to ensure we include all in each config
    all_edges = root.edges
    all_configs = set()  # Use a set instead of list to eliminate duplicates
    stack = [(root, {})]

    while stack:
        current_node, current_decisions = stack.pop()

        if isinstance(current_node, InliningTreeLeaf):
            # Create a complete configuration with all edges
            config = []
            for edge in sorted(all_edges):  # Sort edges for consistent ordering
                decision = current_decisions.get(edge, "no-inline")
                config.append(
                    {"src": edge[0], "dest": edge[1], "inlined": decision == "inline"}
                )
            # Convert config to hashable format (tuple of tuples)
            hashable_config = tuple((d["src"], d["dest"], d["inlined"]) for d in config)
            all_configs.add(hashable_config)
            continue

        elif isinstance(current_node, InliningTreeBinaryNode):
            partition_edge = current_node.partition_edge

            decisions_not_inlined = copy.deepcopy(current_decisions)
            decisions_not_inlined[partition_edge] = "no-inline"
            stack.append((current_node.not_inlined, decisions_not_inlined))

            decisions_inlined = copy.deepcopy(current_decisions)
            decisions_inlined[partition_edge] = "inline"
            stack.append((current_node.inlined, decisions_inlined))

        elif isinstance(current_node, InliningTreeComponentsNode):
            component_configs = []
            for component in current_node.components:
                sub_configs = collect_all_configurations_iterative(component)
                component_configs.append(sub_configs)

            from itertools import product

            for config_tuple in product(*component_configs):
                # Merge decisions from all components
                merged_decisions = {}
                for component_config in config_tuple:
                    for decision in component_config:
                        edge = (decision["src"], decision["dest"])
                        merged_decisions[edge] = (
                            "inline" if decision["inlined"] else "no-inline"
                        )

                # Create complete configuration with all edges
                config = []
                for edge in all_edges:
                    decision = merged_decisions.get(edge, "no-inline")
                    config.append(
                        {
                            "src": edge[0],
                            "dest": edge[1],
                            "inlined": decision == "inline",
                        }
                    )
                all_configs.add(
                    tuple((d["src"], d["dest"], d["inlined"]) for d in config)
                )

    # Convert hashable configs back to the original format
    return [
        [
            {"src": src, "dest": dest, "inlined": inlined}
            for src, dest, inlined in config
        ]
        for config in all_configs
    ]


csv_path = Path(__file__).parent / "optimal_configs.csv"


def get_optimal_program_size_inline_config(
    _: Dict, name: str
) -> Dict[Tuple[str, str], bool]:
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["program_name"] == name:
                return ast.literal_eval(row["best_program_size_config"])
    return {}


def get_optimal_instruction_count_inline_config(
    _: Dict, name: str
) -> Dict[Tuple[str, str], bool]:
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["program_name"] == name:
                return ast.literal_eval(row["best_executed_instr_count_config"])
    return {}
