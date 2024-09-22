import json
import sys
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


def constant_propagation(fn):
    blocks = form_blocks(fn)

    q, ins, outs = set(), [], []
    for i in range(len(blocks)):
        q.add(i)
        ins.append({})
        outs.append({})

    while len(q) > 0:
        id = q.pop()
        block = blocks[id]
        ins[id] = meet([outs[p] for p in block["predecessors"]])
        original_outs = outs[id].copy()
        outs[id] = f(block, ins[id])
        if outs[id] != original_outs:
            for succ in block["successors"]:
                q.add(succ)


def apply_constant_propagation(fn):
    blocks = form_blocks(fn)

    for block in blocks:
        for instr in block["instrs"]:
            if "args" in instr and instr["op"] not in ["br", "jmp", "ret"]:
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

    for block in blocks:
        for instr in block["instrs"]:
            if "state" in instr:
                del instr["state"]

    fn["instrs"] = [instr for block in blocks for instr in block["instrs"]]


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        constant_propagation(fn)
        apply_constant_propagation(fn)
    json.dump(prog, sys.stdout, indent=2)
