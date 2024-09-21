import json
import sys

from utils.form_blocks import form_blocks
from utils.instr import is_side_effect_free, get_args_set, get_dest


def local_dce(fn):
    blocks = form_blocks(fn)
    for block in blocks:
        unused = {}
        for inst in block["instrs"]:
            for use in get_args_set(inst):
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
