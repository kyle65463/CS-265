import json
import sys
from collections import defaultdict


def is_side_effect_free(instr):
    side_effect_ops = {
        "jmp",
        "br",
        "call",
        "ret",
        "print",
        "nop",
        "store",
        "free",
        "speculate",
        "commit",
        "guard",
    }
    return "op" in instr and instr["op"] not in side_effect_ops


def get_args(instr):
    if "args" in instr:
        return set(instr["args"])
    return set()


def get_dest(instr):
    if "dest" in instr:
        return instr["dest"]
    return None


def global_dce(fn):
    instrs = []
    for idx, instr in enumerate(fn["instrs"]):
        instr_with_id = instr.copy()
        instr_with_id["id"] = idx
        instrs.append(instr_with_id)

    used = defaultdict(set)
    for instr in instrs:
        for arg in get_args(instr):
            # Keep track of the instructions that use each argument
            used[arg].add(instr["id"])

    removing_instrs = {}
    for instr in reversed(instrs):
        if len(used[get_dest(instr)]) == 0 and is_side_effect_free(instr):
            # Remove the instruction
            removing_instrs[instr["id"]] = True
            # Remove the instruction id from the used set
            for arg in get_args(instr):
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
