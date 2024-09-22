import copy
import json
import sys
from utils.dataflow import forward_df
from utils.form_blocks import form_blocks


def infer_type(value):
    if isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    else:
        return "int"


def meet(pred_outs):
    if len(pred_outs) == 0:
        return {}
    out = pred_outs[0].copy()
    for pred in pred_outs[1:]:
        for key, val in pred.items():
            if key in out:
                if out[key] != val:
                    out[key] = "?"
            else:
                out[key] = val
    return out


def f(block, i):
    out = i.copy()
    for instr in block["instrs"]:
        instr["state"] = out.copy()
        if "dest" in instr:
            dest = instr["dest"]
            if dest in out and out[dest] == "?":
                out[dest] = "?"
            elif "value" in instr:
                out[dest] = instr["value"]
            elif "op" in instr and instr["op"] == "id":
                if instr["args"][0] in out and out[instr["args"][0]] != "?":
                    out[dest] = out[instr["args"][0]]
                else:
                    out[dest] = "?"
            else:
                out[dest] = "?"
        if "op" in instr and instr["op"] in ["br", "jmp", "ret"]:
            break
    return out


def find_block_by_label(blocks, label):
    for block in blocks:
        if block["label"] == label:
            return block
    return None


def constant_propagation(fn):
    blocks = form_blocks(fn)

    processed_blocks = set()
    live_blocks = [blocks[0]]
    while len(live_blocks) > 0:
        block = live_blocks.pop()
        if block["id"] in processed_blocks:
            continue
        processed_blocks.add(block["id"])
        has_const_branch = False
        for instr in block["instrs"]:
            if "args" in instr:
                all_args_constant = all(
                    arg in instr["state"] and instr["state"][arg] != "?"
                    for arg in instr["args"]
                )
                if all_args_constant:
                    # Fold constants
                    const_args = [instr["state"][arg] for arg in instr["args"]]
                    if instr["op"] in ["add", "sub", "mul", "div"]:
                        a, b = const_args[0], const_args[1]
                        if instr["op"] == "add":
                            result = a + b
                        elif instr["op"] == "sub":
                            result = a - b
                        elif instr["op"] == "mul":
                            result = a * b
                        elif instr["op"] == "div":
                            result = a // b
                        instr["op"] = "const"
                        instr["value"] = result
                        del instr["args"]
                    elif instr["op"] in ["eq", "lt", "gt", "le", "ge", "ne"]:
                        a, b = const_args[0], const_args[1]
                        if instr["op"] == "eq":
                            result = a == b
                        elif instr["op"] == "lt":
                            result = a < b
                        elif instr["op"] == "gt":
                            result = a > b
                        elif instr["op"] == "le":
                            result = a <= b
                        elif instr["op"] == "ge":
                            result = a >= b
                        elif instr["op"] == "ne":
                            result = a != b
                        instr["op"] = "const"
                        instr["value"] = result
                        instr["type"] = "bool"
                        del instr["args"]
                    elif instr["op"] == "id":
                        instr["op"] = "const"
                        instr["value"] = const_args[0]
                        del instr["args"]
                    elif instr["op"] == "br":
                        has_const_branch = True
                        cond = const_args[0]
                        label = instr["labels"][0] if cond else instr["labels"][1]
                        next_block = find_block_by_label(blocks, label)
                        live_blocks.append(next_block)
                        instr["op"] = "jmp"
                        instr["labels"] = [label]
                        del instr["args"]

        if not has_const_branch:
            for succ in block["successors"]:
                live_blocks.append(blocks[succ])

    blocks = [block for block in blocks if block["id"] in processed_blocks]
    for block in blocks:
        for instr in block["instrs"]:
            if "state" in instr:
                del instr["state"]

    fn["instrs"] = [instr for block in blocks for instr in block["instrs"]]


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        forward_df(fn, f, meet)
        constant_propagation(fn)
        while True:
            old_fn = copy.deepcopy(fn)
            forward_df(fn, f, meet)
            constant_propagation(fn)
            if fn == old_fn:
                break
    json.dump(prog, sys.stdout, indent=2)
