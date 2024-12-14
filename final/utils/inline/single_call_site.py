from typing import Dict
from utils.inline.graph import find_recursive_functions, form_call_graph


def get_single_call_site_inline_config(prog: Dict) -> Dict:
    _, edges = form_call_graph(prog)
    recursive = find_recursive_functions(edges)

    call_sites = {}
    for func in prog["functions"]:
        call_sites[func["name"]] = 0

    # Count call sites for each function
    for func in prog["functions"]:
        for instr in func["instrs"]:
            if "op" in instr and instr["op"] == "call":
                callee = instr["funcs"][0]
                call_sites[callee] += 1

    config = {
        (src, dest): True
        for src, dest in edges
        if (src not in recursive or dest not in recursive) and call_sites[dest] == 1
    }

    return config
