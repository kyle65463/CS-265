import json
import sys

from utils.alias import alias_analysis
from utils.legacy.dataflow import forward_df

all_memory_locations = set()


def store_forwarding_f(block, in_state):
    out_state = in_state.copy()
    for instr in block["instrs"]:
        instr["store_map"] = out_state.copy()
        if "op" not in instr:
            continue
        op = instr["op"]
        if op == "store":
            p = instr["args"][0]
            v = instr["args"][1]
            pts_p = instr["alias"].get(p, all_memory_locations)
            for l in pts_p:
                out_state[l] = v
        elif op == "load":
            pass
        elif op == "call":
            # Invalidate all mappings
            for l in all_memory_locations:
                out_state[l] = None
    return out_state


def store_forwarding_meet(preds):
    if not preds:
        return {}
    result = preds[0].copy()
    for pred in preds[1:]:
        for l in all_memory_locations:
            v1 = result.get(l, None)
            v2 = pred.get(l, None)
            if v1 == v2:
                continue
            else:
                result[l] = None
    return result


def store_forwarding(fn):
    new_instrs = []
    for instr in fn["instrs"]:
        if "op" not in instr:
            new_instrs.append(instr)
            continue
        op = instr["op"]
        if op == "load":
            dest = instr["dest"]
            p = instr["args"][0]
            pts_p = instr["alias"].get(p, all_memory_locations)
            store_map = instr["store_map"]
            # Check if p points to a unique memory location with a known value
            if len(pts_p) == 1:
                l = next(iter(pts_p))
                v = store_map.get(l, None)
                if v is not None:
                    new_instr = {
                        "dest": dest,
                        "type": instr["type"],
                        "op": "const" if isinstance(v, (int, float)) else "id",
                        "value": v if isinstance(v, (int, float)) else None,
                        "args": [] if isinstance(v, (int, float)) else [v],
                    }
                    new_instrs.append(new_instr)
                    continue
        new_instrs.append(instr)
    fn["instrs"] = new_instrs


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        all_memory_locations = alias_analysis(fn)

        forward_df(fn, store_forwarding_f, store_forwarding_meet, initial_value={})
        store_forwarding(fn)

        for instr in fn["instrs"]:
            if "alias" in instr:
                del instr["alias"]
    json.dump(prog, sys.stdout, indent=2)
