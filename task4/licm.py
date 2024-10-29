import json
import sys
from copy import deepcopy
from utils.loop import get_natural_loops
from utils.cfg import convert_blocks_to_fn, form_blocks


def is_deterministic(instr):
    non_deterministic_ops = [
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
        "phi",
        "alloc",
        "ptradd",
        "load",
    ]
    return "op" in instr and instr["op"] and instr["op"] not in non_deterministic_ops


def licm(fn):
    cfg, blocks = form_blocks(fn)
    cfg, blocks = deepcopy(cfg), deepcopy(blocks)
    loops = get_natural_loops(fn)

    for loop in loops:
        if loop["preheader"] is None:
            continue

        loop_blocks = set(loop["blocks"])
        invariant_args = set()

        # find dest defined outside the loop
        for block in blocks:
            if block["name"] not in loop_blocks:
                for instr in block["instrs"]:
                    if "dest" in instr:
                        invariant_args.add(instr["dest"])
        if "args" in fn:
            for arg in fn["args"]:
                invariant_args.add(arg["name"])

        # find loop-invariant instructions inside the loop
        changed = True
        invariant_instrs = []
        while changed:
            changed = False
            for block_name in loop_blocks:
                block = cfg[block_name]
                for instr in block["instrs"]:
                    if "dest" in instr and instr["dest"] not in invariant_args:
                        if all(arg in invariant_args for arg in instr.get("args", [])):
                            if is_deterministic(instr):
                                invariant_args.add(instr["dest"])
                                invariant_instrs.append(instr)
                                changed = True

        if len(invariant_instrs) == 0:
            continue

        # move invariant instructions to the preheader
        preheader = loop["preheader"]
        preheader_block = cfg[preheader]
        preheader_block["instrs"] = (
            [preheader_block["instrs"][0]]  # label
            + invariant_instrs
            + preheader_block["instrs"][1:]  # rest of the instructions
        )
        preheader_index = next(
            i for i, block in enumerate(blocks) if block["name"] == preheader
        )
        blocks[preheader_index] = preheader_block

        # remove invariant instructions from loop blocks
        for block_name in loop_blocks:
            block = cfg[block_name]
            for invariant_instr in invariant_instrs:
                if invariant_instr in block["instrs"]:
                    block["instrs"].remove(invariant_instr)
            block_index = next(
                i for i, block in enumerate(blocks) if block["name"] == block_name
            )
            blocks[block_index] = block

    return convert_blocks_to_fn(blocks, fn)


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        new_fn = licm(fn)
        fn["instrs"] = new_fn["instrs"]
    print(json.dumps(prog, indent=2))
