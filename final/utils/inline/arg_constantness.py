from typing import Dict
from utils.inline.graph import find_recursive_functions, form_call_graph
from constant import forward_df, f, meet


def get_arg_constantness_inline_config(prog: Dict) -> Dict:
    _, edges = form_call_graph(prog)
    recursive = find_recursive_functions(edges)

    # Run constant propagation on all functions
    for func in prog["functions"]:
        forward_df(func, f, meet)

    # Check each function's call sites
    config = {}
    for func in prog["functions"]:
        for instr in func["instrs"]:
            if "op" in instr and instr["op"] == "call":
                callee = instr["funcs"][0]

                # Skip recursive calls
                if func["name"] in recursive and callee in recursive:
                    continue

                # Check if any arguments are constant
                has_constant_arg = False
                if "args" in instr and "state" in instr:
                    for arg in instr["args"]:
                        if arg in instr["state"] and instr["state"][arg] != "?":
                            has_constant_arg = True
                            break

                if has_constant_arg:
                    config[(func["name"], callee)] = True

    return config
