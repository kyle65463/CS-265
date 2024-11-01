import json
import sys

from utils.alias import alias_analysis
from utils.legacy.dataflow import backward_df


all_memory_locations = set()


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
        all_memory_locations = alias_analysis(fn)
        backward_df(fn, liveness_f, liveness_meet, initial_value=set())
        dead_store_elimination(fn)
        for instr in fn["instrs"]:
            del instr["live_mem"]
            del instr["alias"]
    json.dump(prog, sys.stdout, indent=2)
