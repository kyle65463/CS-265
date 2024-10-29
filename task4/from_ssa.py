from collections import defaultdict
import json
import sys
from utils.cfg import convert_blocks_to_fn, form_blocks

TERMINATORS = {"br", "jmp", "ret"}


def from_ssa(fn):
    _, blocks = form_blocks(fn)

    phis = {block["name"]: [] for block in blocks}
    for block in blocks:
        remove_phis = []
        for instr in block["instrs"]:
            if "op" in instr and "dest" in instr and instr["op"] == "phi":
                dest = instr["dest"]
                for label, arg in zip(instr["labels"], instr["args"]):
                    phis[label].append((dest, arg, instr["type"]))
                remove_phis.append(instr)
        for instr in remove_phis:
            block["instrs"].remove(instr)
    
    for block in blocks:
        for dest, arg, type in phis[block["name"]]:
            if arg == "__undefined":
                continue
            insert_index = len(block["instrs"])
            if len(block["instrs"]) > 0 and block["instrs"][-1]["op"] in TERMINATORS:
                insert_index = len(block["instrs"]) - 1
            block["instrs"].insert(
                insert_index,
                {
                    "op": "id",
                    "dest": dest,
                    "type": type,
                    "args": [arg],
                },
            )

    return convert_blocks_to_fn(blocks, fn)


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        new_fn = from_ssa(fn)
        fn["instrs"] = new_fn["instrs"]
    print(json.dumps(prog, indent=2))