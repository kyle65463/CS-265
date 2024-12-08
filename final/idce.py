import json
import sys
from typing import Dict, Set
from utils.inline.graph import form_call_graph


def find_reachable_functions(prog: Dict) -> Set[str]:
    """
    Identifies all functions reachable from the main function using DFS.
    """
    nodes, _ = form_call_graph(prog)

    # Start from main function
    reachable = set()
    worklist = ["main"]  # Assuming 'main' is the entry point

    while worklist:
        func_name = worklist.pop()
        if func_name not in reachable and func_name in nodes:
            reachable.add(func_name)
            # Add all called functions to the worklist
            worklist.extend(nodes[func_name]["edges"])

    return reachable


def idce(prog: Dict) -> Dict:
    reachable = find_reachable_functions(prog)

    # Keep only reachable functions
    prog["functions"] = [
        func for func in prog["functions"] if func["name"] in reachable
    ]

    return prog


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    prog = idce(prog)
    print(json.dumps(prog, indent=2))
