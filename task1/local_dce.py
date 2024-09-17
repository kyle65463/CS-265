import json
import sys

TERMINATORS = {"br", "jmp", "ret"}


def form_blocks(fn):
    blocks = []
    cur_instrs = []
    for instr in fn["instrs"]:
        if "label" in instr:
            # Start a new block
            if len(cur_instrs) > 0:
                blocks.append(
                    {
                        "instrs": cur_instrs,
                    }
                )
            cur_instrs = [instr]
        elif "op" in instr:
            cur_instrs.append(instr)
            if instr["op"] in TERMINATORS:
                blocks.append(
                    {
                        "instrs": cur_instrs,
                    }
                )
                cur_instrs = []
    if len(cur_instrs) > 0:
        blocks.append({"instrs": cur_instrs})
    return blocks


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


def local_dce(fn):
    blocks = form_blocks(fn)
    for block in blocks:
        unused = {}
        for inst in block["instrs"]:
            for use in get_args(inst):
                if use in unused:
                    del unused[use]
            dest = get_dest(inst)
            if dest:
                if dest in unused:
                    block["instrs"].remove(unused[dest])
                if is_side_effect_free(inst):
                    unused[dest] = inst

    fn["instrs"] = [instr for block in blocks for instr in block["instrs"]]


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        local_dce(fn)
    json.dump(prog, sys.stdout, indent=2)
