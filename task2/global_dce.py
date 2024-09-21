import json
import sys
from collections import defaultdict
from utils.instr import is_side_effect_free, get_args_set, get_dest


def global_dce(fn):
    instrs = []
    for idx, instr in enumerate(fn["instrs"]):
        instr_with_id = instr.copy()
        instr_with_id["id"] = idx
        instrs.append(instr_with_id)

    used = defaultdict(set)
    for instr in instrs:
        for arg in get_args_set(instr):
            # Keep track of the instructions that use each argument
            used[arg].add(instr["id"])

    removing_instrs = {}
    for instr in reversed(instrs):
        if len(used[get_dest(instr)]) == 0 and is_side_effect_free(instr):
            # Remove the instruction
            removing_instrs[instr["id"]] = True
            # Remove the instruction id from the used set
            for arg in get_args_set(instr):
                used[arg].remove(instr["id"])

    # Filter out the instructions that are being removed
    instrs = [instr for instr in instrs if instr["id"] not in removing_instrs]
    for instr in instrs:
        instr.pop("id", None)

    fn["instrs"] = instrs


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        global_dce(fn)
    json.dump(prog, sys.stdout, indent=2)
