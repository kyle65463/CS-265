from typing import Dict
from utils.inline.graph import find_recursive_functions, form_call_graph
from utils.legacy.loop import get_natural_loops
from utils.legacy.cfg import form_blocks


def get_in_loop_inline_config(prog: Dict) -> Dict:
    _, edges = form_call_graph(prog)
    recursive = find_recursive_functions(edges)

    # Track which function calls are inside loops
    calls_in_loops = set()

    # For each function, analyze its loops and instructions
    for func in prog["functions"]:
        # Get all natural loops in the function
        loops = get_natural_loops(func)
        loop_blocks = set()
        for loop in loops:
            loop_blocks.update(loop["blocks"])

        # Get the CFG to map instructions to blocks
        _, blocks = form_blocks(func)

        # Check each instruction for calls and whether they're in loop blocks
        for block in blocks:
            in_loop = block["name"] in loop_blocks
            for instr in block["instrs"]:
                if in_loop and instr.get("op") == "call":
                    for callee in instr.get("funcs", []):
                        calls_in_loops.add((func["name"], callee))

    # Only inline function calls that are NOT in loops and not recursive
    config = {
        (src, dest): True
        for src, dest in edges
        if (src, dest) in calls_in_loops
        and (src not in recursive or dest not in recursive)
    }

    return config
