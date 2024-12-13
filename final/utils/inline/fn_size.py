from typing import Dict
from utils.inline.graph import find_recursive_functions, form_call_graph


def get_fn_size_inline_config(prog: Dict, size_threshold: str) -> Dict:
    nodes, edges = form_call_graph(prog)

    # Find recursive functions
    recursive = find_recursive_functions(edges)

    fn_size = {}
    for node in nodes:
        for fn in prog["functions"]:
            if fn["name"] == node:
                fn_size[node] = len(fn["instrs"])

    # Only inline non-recursive function calls where the callee is small enough
    config = {
        (src, dest): True
        for src, dest in edges
        if (src not in recursive or dest not in recursive)
        and fn_size[dest] <= int(size_threshold)
    }

    return config
