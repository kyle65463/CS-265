import json
import sys
from utils.dataflow import forward_df
from utils.instr import get_dest


def meet(pred_outs):
    if len(pred_outs) == 0:
        return set()
    return pred_outs[0].union(*pred_outs[1:])


def f(block, i):
    out = set(i)
    for instr in block["instrs"]:
        dest = get_dest(instr)
        if dest is not None:
            out.add(dest)
    return out


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        forward_df(fn, f, meet, initial_value=set(), print_result=True)
