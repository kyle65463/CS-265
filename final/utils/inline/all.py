from typing import Dict

from utils.inline.graph import find_recursive_functions, form_call_graph


def get_all_inline_config(prog: Dict) -> Dict:
    _, edges = form_call_graph(prog)

    # Find recursive functions
    recursive = find_recursive_functions(edges)

    # Only inline non-recursive function calls
    config = {
        (src, dest): True
        for src, dest in edges
        if src not in recursive or dest not in recursive
    }

    return config
