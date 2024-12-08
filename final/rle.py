import json
import sys

from utils.alias import alias_analysis
from utils.legacy.dataflow import forward_df

all_memory_locations = set()

def redundant_load_elimination_f(block, in_state):
    out_state = in_state.copy()
    for instr in block["instrs"]:
        instr["load_map"] = out_state.copy()
        if "op" not in instr:
            continue
        op = instr["op"]
        
        if "dest" in instr:
            dest = instr["dest"]
            keys_to_invalidate = [l for l, var in out_state.items() if var == dest]
            for l in keys_to_invalidate:
                del out_state[l]
        
        if op == "load":
            dest = instr["dest"]
            p = instr["args"][0]
            pts_p = instr["alias"].get(p, all_memory_locations)
            # Check if we have a mapping for all memory locations in pts_p
            can_replace = True
            previous_vars = set()
            for l in pts_p:
                if l in out_state:
                    previous_vars.add(out_state[l])
                else:
                    can_replace = False
                    break
            if can_replace and len(previous_vars) == 1:
                # All memory locations map to the same variable
                prev_var = next(iter(previous_vars))
                instr["redundant_load"] = prev_var
            else:
                # Update the mapping
                for l in pts_p:
                    out_state[l] = dest
        elif op == "store":
            p = instr["args"][0]
            pts_p = instr["alias"].get(p, all_memory_locations)
            for l in pts_p:
                if l in out_state:
                    del out_state[l]
        elif op == "call":
            # Invalidate all mappings
            out_state.clear()
    return out_state


def redundant_load_elimination_meet(preds):
    if not preds:
        return {}
    result = preds[0].copy()
    for pred in preds[1:]:
        keys = set(result.keys()) | set(pred.keys())
        for l in keys:
            v1 = result.get(l, None)
            v2 = pred.get(l, None)
            if v1 == v2 and v1 is not None:
                continue
            else:
                if l in result:
                    del result[l]
    return result

def redundant_load_elimination(fn):
    new_instrs = []
    for instr in fn["instrs"]:
        if "op" not in instr:
            new_instrs.append(instr)
            continue
        if instr["op"] == "load" and "redundant_load" in instr:
            dest = instr["dest"]
            prev_var = instr["redundant_load"]
            new_instr = {
                "dest": dest,
                "type": instr["type"],
                "op": "id",
                "args": [prev_var],
            }
            new_instrs.append(new_instr)
            continue
        new_instrs.append(instr)
    fn["instrs"] = new_instrs

if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        all_memory_locations = alias_analysis(fn)
        forward_df(fn, redundant_load_elimination_f, redundant_load_elimination_meet, initial_value={})
        redundant_load_elimination(fn)
        for instr in fn["instrs"]:
            instr.pop("alias", None)
            instr.pop("load_map", None)
            instr.pop("redundant_load", None)
    json.dump(prog, sys.stdout, indent=2)
