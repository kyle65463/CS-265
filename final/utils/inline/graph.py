from typing import Dict, List, Set, Tuple


def form_call_graph(prog: Dict) -> Tuple[Dict, List[Tuple[str, str]]]:
    nodes = {}
    edges = []
    for fn in prog["functions"]:
        name = fn["name"]
        nodes[name] = {
            "name": name,
            "edges": [],
        }
        for instr in fn["instrs"]:
            if "op" in instr and instr["op"] == "call":
                callee = instr["funcs"][0]
                nodes[name]["edges"].append(callee)
    # Deduplicate edges
    for name, data in nodes.items():
        data["edges"] = list(set(data["edges"]))
        for e in data["edges"]:
            edges.append((name, e))

    edges = list(set(edges))
    return nodes, edges


def find_recursive_functions(edges: List[tuple]) -> Set[str]:
    # Build adjacency list
    graph = {}
    for src, dest in edges:
        if src not in graph:
            graph[src] = set()
        graph[src].add(dest)

    # Find functions that are part of cycles (recursive)
    recursive = set()
    visited = set()
    path = set()

    def dfs(node):
        if node in path:
            recursive.add(node)
            return
        if node in visited:
            return

        visited.add(node)
        path.add(node)

        for neighbor in graph.get(node, []):
            dfs(neighbor)

        path.remove(node)

    for node in graph:
        dfs(node)

    return recursive
