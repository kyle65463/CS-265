from typing import List, Dict, Set

from utils.inline.graph import form_call_graph


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


def get_all_inline_config(prog: Dict) -> List[Dict]:
    _, edges = form_call_graph(prog)

    # Find recursive functions
    recursive = find_recursive_functions(edges)

    # Only inline non-recursive function calls
    config = [
        {"src": src, "dest": dest, "inlined": True}
        for src, dest in edges
        if src not in recursive or dest not in recursive
    ]

    return config
