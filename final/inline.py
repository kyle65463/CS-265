import json
import sys
import uuid

from utils.inline.arg_constantness import get_arg_constantness_inline_config
from utils.inline.single_call_site import get_single_call_site_inline_config
from utils.inline.in_loop import get_in_loop_inline_config
from utils.inline.all import get_all_inline_config
from utils.inline.fn_size import get_fn_size_inline_config
from utils.inline.optimal import (
    get_optimal_instruction_count_inline_config,
    get_optimal_program_size_inline_config,
)

get_inline_config = {
    "all": get_all_inline_config,
    "optimal_ps": get_optimal_program_size_inline_config,
    "optimal_ic": get_optimal_instruction_count_inline_config,
    "fn_size": get_fn_size_inline_config,
    "in_loop": get_in_loop_inline_config,
    "single_call_site": get_single_call_site_inline_config,
    "arg_constantness": get_arg_constantness_inline_config,
}


def inline(prog: dict, config: dict[tuple[str, str], bool]):
    """
    Inline the program using the given configuration.

    Args:
        prog: The program to inline.
        config: The configuration to use for inlining. A dictionary where:
            - key: Tuple of (source_function, destination_function) names
            - value: Boolean indicating whether to inline this call

    Returns:
        The inlined program.
    """
    # Process each function in the program
    for fn in prog["functions"]:
        new_instrs = []

        for i in range(len(fn["instrs"])):
            instr = fn["instrs"][i]

            # Handle non-call instructions
            if "op" not in instr or instr["op"] != "call":
                new_instrs.append(instr)
                continue

            # Get the called function name
            callee_name = instr["funcs"][0]

            # Check if this call should be inlined based on config
            should_inline = config.get((fn["name"], callee_name), False)

            if not should_inline:
                new_instrs.append(instr)
                continue

            # Find the called function
            callee = None
            for func in prog["functions"]:
                if func["name"] == callee_name:
                    callee = func
                    break

            if not callee:
                new_instrs.append(instr)
                continue

            # Check if function has multiple returns
            has_multiple_returns = False
            return_count = 0
            for callee_instr in callee["instrs"]:
                if "op" in callee_instr and callee_instr["op"] == "ret":
                    return_count += 1
                    if return_count > 1:
                        has_multiple_returns = True
                        break

            # Create unique suffix for this inline instance
            inline_suffix = str(uuid.uuid4())[:8]
            var_map = {}

            # Add done label only if multiple returns
            done_label = None
            if has_multiple_returns:
                done_label = f"inline_done_{inline_suffix}"

            # Find parameters that get modified in the callee
            modified_params = set()
            for callee_instr in callee["instrs"]:
                if "dest" in callee_instr:
                    for param in callee.get("args", []):
                        if callee_instr["dest"] == param["name"]:
                            modified_params.add(param["name"])

            # Map arguments to parameters, creating copies only for modified parameters
            if "args" in instr:
                for arg, param in zip(instr["args"], callee.get("args", [])):
                    if param["name"] in modified_params:
                        # Create a copy only if the parameter gets modified
                        arg_copy = f"{arg}_{inline_suffix}"
                        new_instrs.append(
                            {
                                "op": "id",
                                "dest": arg_copy,
                                "type": param.get("type"),
                                "args": [arg],
                            }
                        )
                        var_map[param["name"]] = arg_copy
                    else:
                        # Use the original argument directly if it's not modified
                        var_map[param["name"]] = arg

            # Inline the function body
            for callee_instr in callee["instrs"]:
                if "op" not in callee_instr:
                    new_label = {"label": f"{callee_instr['label']}_{inline_suffix}"}
                    new_instrs.append(new_label)
                    continue

                # Create a copy of the instruction
                new_instr = callee_instr.copy()

                # Update label references in instructions
                if "labels" in new_instr:
                    new_instr["labels"] = [
                        f"{label}_{inline_suffix}" for label in new_instr["labels"]
                    ]

                # Remap variable names with random suffix
                if "dest" in new_instr:
                    if new_instr["dest"] not in var_map:
                        var_map[new_instr["dest"]] = (
                            f"inline_{new_instr['dest']}_{inline_suffix}"
                        )
                    new_instr["dest"] = var_map[new_instr["dest"]]

                if "args" in new_instr:
                    new_instr["args"] = [
                        var_map.get(arg, arg) for arg in new_instr["args"]
                    ]

                # Handle return value
                if new_instr["op"] == "ret":
                    if "args" in new_instr and "dest" in instr:
                        ret_val = new_instr["args"][0]
                        new_instrs.append(
                            {
                                "op": "id",
                                "dest": instr["dest"],
                                "type": instr["type"],
                                "args": [var_map.get(ret_val, ret_val)],
                            }
                        )

                    # Add jump if there are multiple returns
                    if has_multiple_returns:
                        new_instrs.append(
                            {
                                "op": "jmp",
                                "labels": [done_label],
                            }
                        )
                    continue

                new_instrs.append(new_instr)

            # Add the done label after inlined instructions if needed
            if has_multiple_returns:
                new_instrs.append({"label": done_label})

        fn["instrs"] = new_instrs

    return prog


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in get_inline_config:
        print(f"Usage: {sys.argv[0]} <strategy>")
        print(f"Available strategies: {', '.join(get_inline_config.keys())}")
        sys.exit(1)

    strategy = sys.argv[1]
    prog = json.load(sys.stdin)
    config = get_inline_config[strategy](prog, *sys.argv[2:])
    prog = inline(prog, config)
    print(json.dumps(prog, indent=2))
