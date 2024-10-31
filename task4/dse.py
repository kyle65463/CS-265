import json
import sys

from utils.legacy.form_blocks import form_blocks
from utils.legacy.dataflow import backward_df, forward_df

all_memory_locations = set()
ext_memory_locations = {}

def memory_locations_from_args(fn):
    mem_locs = {}
    for arg in fn.get("args", []):
        if "ptr" in arg["type"]:
            arg_name = arg["name"]
            mem_locs[arg_name] = set([f"unknown_{fn['name']}_{arg_name}"])
    return mem_locs

def collect_memory_locations(fn):
    blocks = form_blocks(fn)

    memory_locations = set()
    ext_mem_locs = memory_locations_from_args(fn)
    for _, mem_locs in ext_mem_locs.items():
        memory_locations.update(mem_locs)

    for block in blocks:
        for i, instr in enumerate(block["instrs"]):
            if "op" in instr:
                op = instr["op"]
                if op == "alloc":
                    alloc_site = f"alloc_{block['id']}_{i}"
                    memory_locations.add(alloc_site)
                elif op == "ptradd":
                    unknown_loc = f"unknown_{block['id']}_{i}"
                    memory_locations.add(unknown_loc)
                # handle load?
    return memory_locations


def alias_meet(pred_outs):
    """Union of points-to sets for each variable"""
    if len(pred_outs) == 0:
        return ext_memory_locations.copy()

    result = pred_outs[0].copy()
    for pred in pred_outs[1:]:
        for var, locations in pred.items():
            if var in result:
                result[var] = result[var].union(locations)
            else:
                result[var] = locations.copy()
    return result


def alias_f(block, in_state):
    """Transfer function for pointer analysis"""
    out = in_state.copy()

    # Track allocation sites by instruction index
    for i, instr in enumerate(block["instrs"]):
        instr["alias"] = out.copy()
        if "dest" in instr:
            dest = instr["dest"]
            op = instr["op"]
            if op == "alloc":
                alloc_site = f"alloc_{block['id']}_{i}"
                out[dest] = {alloc_site}
            elif op == "id" and "ptr" in instr["type"]:
                src = instr["args"][0]
                out[dest] = out.get(src, all_memory_locations).copy()
            elif op == "ptradd":
                base_ptr = instr["args"][0]
                offset = instr["args"][1]
                base_pts = out.get(base_ptr, all_memory_locations).copy()
                # Since we don't know the offset, conservatively assume dest may point
                # to base_ptr's locations and also to new locations.
                new_location = f"unknown_{block['id']}_{i}"
                out[dest] = base_pts.union({new_location})
            elif op == "call" and "ptr" in instr["type"]:
                new_location = f"unknown_{block['id']}_{i}"
                out[dest] = all_memory_locations.union({new_location})
            elif op in ["load", "store"]:
                out[dest] = all_memory_locations.copy()
    return out


def liveness_meet(succ_ins):
    if len(succ_ins) == 0:
        return all_memory_locations.copy()
    return succ_ins[0].union(*succ_ins[1:])


def liveness_f(block, out_state: set):
    in_state = out_state.copy()
    instrs = block["instrs"]
    for instr in reversed(instrs):
        instr["live_mem"] = in_state.copy()
        if "op" not in instr:
            continue
        if instr["op"] == "load":
            p = instr["args"][0]
            pts_p = instr["alias"].get(p, all_memory_locations)
            in_state.update(pts_p)
        elif instr["op"] == "store":
            p = instr["args"][0]
            pts_p = instr["alias"].get(p, all_memory_locations)
            if len(pts_p) == 1:
                in_state.difference_update(pts_p)
    return in_state


def dead_store_elimination(fn):
    new_instrs = []
    for instr in fn["instrs"]:
        if "op" not in instr:
            new_instrs.append(instr)
            continue
        if instr["op"] == "store":
            p = instr["args"][0]
            pts_p = instr["alias"].get(p, all_memory_locations)
            live_mem = instr["live_mem"]
            # If the intersection is empty, the store is dead
            if pts_p.isdisjoint(live_mem):
                # Eliminate the store
                continue
        new_instrs.append(instr)
    fn["instrs"] = new_instrs


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        # print(fn["name"])
        all_memory_locations = collect_memory_locations(fn)
        ext_memory_locations = memory_locations_from_args(fn)

        forward_df(fn, alias_f, alias_meet, initial_value={})
        backward_df(fn, liveness_f, liveness_meet, initial_value=set())
        # for instr in fn["instrs"]:
        #     print(instr["alias"])
        #     print(instr["live_mem"])
        #     print()
        dead_store_elimination(fn)
        for instr in fn["instrs"]:
            del instr["live_mem"]
            del instr["alias"]
    json.dump(prog, sys.stdout, indent=2)
