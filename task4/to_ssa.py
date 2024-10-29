from collections import defaultdict
import json
import sys
from utils.cfg import convert_blocks_to_fn, form_blocks
from utils.loop import get_dominators


def get_dom_frontier(fn):
    cfg, blocks = form_blocks(fn)
    doms = get_dominators(cfg, blocks)  # doms[b] = a list of blocks that dominate b
    strict_doms = get_dominators(cfg, blocks, strict=True)

    dom_frontiers = {}
    for target_block in blocks:  # A
        A = target_block["name"]
        dom_frontier = []
        for cur_block in blocks:  # B
            B = cur_block["name"]
            if A not in strict_doms[B]:  # A does not strictly dominate B
                has_A_dom_some_pred_of_B = any(
                    A in doms[pred] for pred in cfg[B]["preds"]
                )  # A does dominate some pred of B
                if has_A_dom_some_pred_of_B:
                    dom_frontier.append(B)

        dom_frontiers[A] = dom_frontier

    return dom_frontiers


def get_dom_tree(fn):
    cfg, blocks = form_blocks(fn)
    strict_doms = get_dominators(cfg, blocks, strict=True)

    dom_tree = {
        block["name"]: set() for block in blocks
    }  # key: block name, value: set of blocks that are immediately dominated by the key
    for target_block in blocks:
        A = target_block["name"]
        for cur_block in blocks:
            B = cur_block["name"]
            if A in strict_doms[B] and all(  # A strictly dominates B, and
                A not in strict_doms[C]
                for C in strict_doms[B]
                if C != A
                # A does not strictly dominate any other node that strictly dominates B
            ):
                # A immediately dominates B
                dom_tree[A].add(B)

    return dom_tree


def get_def_blocks_of_vars(fn):
    _, blocks = form_blocks(fn)
    defs, vars = {}, set()
    for block in blocks:
        for instr in block["instrs"]:
            dest = instr.get("dest", None)
            if dest is not None:
                if dest not in defs:
                    defs[dest] = set()
                defs[dest].add(block["name"])
                vars.add(dest)
    return defs, vars


def get_type_of_vars(fn):
    var_types = {arg["name"]: arg["type"] for arg in fn.get("args", [])}
    for instr in fn["instrs"]:
        if "dest" in instr:
            var_types[instr["dest"]] = instr["type"]
    return var_types


def get_phis_locations(fn):
    _, blocks = form_blocks(fn)
    dom_frontiers = get_dom_frontier(fn)
    defs, vars = get_def_blocks_of_vars(fn)

    phis = {
        block["name"]: set() for block in blocks
    }  # key: block name, value: set of variables that needs phis in the block
    for var in vars:
        defining_blocks = list(defs[var])
        for defining_block in defining_blocks:
            for df in dom_frontiers[defining_block]:
                if var not in phis[df]:
                    phis[df].add(var)
                    if df not in defs[var]:
                        defs[var].add(df)
                        defining_blocks.append(df)
    return phis


def convert_to_ssa(fn):
    cfg, blocks = form_blocks(fn)
    var_types = get_type_of_vars(fn)
    phis = get_phis_locations(fn)
    phi_args = {b["name"]: {p: [] for p in phis[b["name"]]} for b in blocks}
    phi_dests = {b["name"]: {p: None for p in phis[b["name"]]} for b in blocks}
    dom_tree = get_dom_tree(fn)
    fn_args = {arg["name"] for arg in fn["args"]} if "args" in fn else set()
    stack = defaultdict(list, {v: [v] for v in fn_args})
    counters = defaultdict(int)

    def fresh_name(var):
        fresh = f"{var}.{counters[var]}"
        counters[var] += 1
        stack[var].insert(0, fresh)
        return fresh

    def rename_phi(block):
        old_stack = {k: list(v) for k, v in stack.items()}

        for phi in phis[block["name"]]:
            phi_dests[block["name"]][phi] = fresh_name(phi)

        for inst in block["instrs"]:
            if "args" in inst:
                new_args = [stack[arg][0] for arg in inst["args"]]
                inst["args"] = new_args

            if "dest" in inst:
                fresh = fresh_name(inst["dest"])
                inst["dest"] = fresh

        for succ in block["succs"]:
            for phi in phis[succ]:
                if stack[phi]:
                    phi_args[succ][phi].append((block["name"], stack[phi][0]))
                else:
                    phi_args[succ][phi].append((block["name"], "__undefined"))

        for child in dom_tree[block["name"]]:
            rename_phi(cfg[child])

        stack.clear()
        stack.update(old_stack)

    rename_phi(cfg[blocks[0]["name"]])

    for block in cfg.values():
        block_name = block["name"]
        for dest, pairs in sorted(phi_args[block_name].items()):
            phi = {
                "op": "phi",
                "dest": phi_dests[block_name][dest],
                "type": var_types[dest],
                "labels": [p[0] for p in pairs],
                "args": [p[1] for p in pairs],
            }
            insert_index = 0
            if len(block["instrs"]) > 0 and "label" in block["instrs"][0]:
                insert_index = 1

            block["instrs"].insert(insert_index, phi)

    return convert_blocks_to_fn(cfg.values(), fn)


def ensure_entry_block_has_no_preds(fn):
    cfg, blocks = form_blocks(fn)
    if len(blocks) == 0:
        return fn

    block = blocks[0]
    if len(block["preds"]) != 0:
        # Add a new entry block
        new_entry_block_name = f"entry.{block['name']}"
        new_entry_block = {
            "name": new_entry_block_name,
            "instrs": [
                {
                    "label": new_entry_block_name,
                }
            ],
            "preds": [],
            "succs": [block["name"]],
        }
        cfg[new_entry_block_name] = new_entry_block
        blocks.insert(0, new_entry_block)
        block["preds"].append(new_entry_block_name)

    for block in blocks[1:]:
        if len(block["preds"]) == 0:
            # remove the block
            blocks.remove(block)

    return convert_blocks_to_fn(blocks, fn)


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        new_fn = ensure_entry_block_has_no_preds(fn)
        fn["instrs"] = new_fn["instrs"]

        new_fn = convert_to_ssa(fn)
        fn["instrs"] = new_fn["instrs"]
    print(json.dumps(prog, indent=2))
