import json
import sys
from utils.dataflow import backward_df
from utils.form_blocks import form_blocks
from utils.instr import get_args_set, get_dest


def meet(succ_ins):
    if len(succ_ins) == 0:
        return set()
    return succ_ins[0].union(*succ_ins[1:])


def f(block, out):
    i = set(out)
    for instr in reversed(block["instrs"]):
        instr["state"] = i.copy()
        dest = get_dest(instr)
        args = get_args_set(instr)
        if dest is not None:
            if dest in i:
                i.discard(dest)
                i.update(args)
        else:
            i.update(args)
    return i


def dead_code_elimination(fn):
    blocks = form_blocks(fn)
    instrs = []
    for block in blocks:
        for instr in block["instrs"]:
            dest = get_dest(instr)
            if dest is not None and dest not in instr["state"]:
                # Remove the instruction
                pass
            else:
                instrs.append(instr)

    for instr in instrs:
        if "state" in instr:
            del instr["state"]

    fn["instrs"] = instrs


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        backward_df(fn, f, meet, initial_value=set())
        dead_code_elimination(fn)
    json.dump(prog, sys.stdout, indent=2)
