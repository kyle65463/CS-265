import json
import sys
from copy import deepcopy
from cfg import convert_blocks_to_fn, form_blocks


def is_jmp(instr):
    return "op" in instr and instr["op"] == "jmp"


def is_br(instr):
    return "op" in instr and instr["op"] == "br"


def get_dominators(cfg, blocks):
    if len(blocks) == 0:
        return {}
    q = [blocks[0]["name"]]
    dom = {}
    while len(q) > 0:
        block_name = q.pop()
        block = cfg[block_name]
        original_dom = deepcopy(dom[block_name]) if block_name in dom else None
        dom[block_name] = set()
        dom[block_name].add(block_name)

        pred_dominators = None
        for pred_name in block["preds"]:
            if pred_dominators is None:
                if pred_name in dom:
                    pred_dominators = dom[pred_name]
                else:
                    pred_dominators = set()
            elif pred_name in dom:
                pred_dominators = pred_dominators.intersection(dom[pred_name])

        if pred_dominators is not None:
            dom[block_name] = dom[block_name].union(pred_dominators)

        if original_dom != dom[block_name]:
            for succ_name in block["succs"]:
                q.append(succ_name)
    for block in blocks:
        if block["name"] not in dom:
            dom[block["name"]] = set()
    for block_name, dom_set in dom.items():
        dom[block_name] = list(dom_set)
    return dom


def get_backedges(cfg, blocks):
    doms = get_dominators(cfg, blocks)
    backedges = []
    for block in blocks:
        block_name = block["name"]
        for succ_name in block["succs"]:
            if succ_name in doms[block_name]:
                backedges.append((block_name, succ_name))
    return backedges


def can_reach_latch_without_header(cfg, blocks, current, visited, latch, header):
    if current == latch:
        return True
    if current == header:
        return False
    visited.add(current)
    for succ in cfg[current]["succs"]:
        if succ not in visited:
            if can_reach_latch_without_header(
                cfg, blocks, succ, visited, latch, header
            ):
                return True
    return False


def get_natural_loops(fn):
    cfg, blocks = form_blocks(fn)
    backedges = get_backedges(cfg, blocks)

    loops = []
    for latch, header in backedges:
        loop = {
            "header": header,
            "latch": latch,
            "blocks": [header],
        }
        for block in blocks:
            if can_reach_latch_without_header(
                cfg, blocks, block["name"], set(), latch, header
            ):
                loop["blocks"].append(block["name"])

        loops.append(loop)
    return loops


def normalize_shared_loops(fn, loops):
    cfg, blocks = form_blocks(fn)
    cfg, blocks = deepcopy(cfg), deepcopy(blocks)

    # group loops by header
    headers2loops = {}  # key: header, value: loop
    for loop in loops:
        if loop["header"] not in headers2loops:
            headers2loops[loop["header"]] = []
        headers2loops[loop["header"]].append(loop)

    new_loops = []
    for header, shared_loops in headers2loops.items():
        if len(shared_loops) > 1:
            # insert a new latch block
            original_latches = [loop["latch"] for loop in shared_loops]
            new_latch = f"{header}_new_latch"
            new_latch_block = {
                "name": new_latch,
                "instrs": [
                    {
                        "label": new_latch,
                    },
                    {
                        "op": "jmp",
                        "args": [],
                        "labels": [header],
                    },
                ],
                "preds": original_latches,
                "succs": [header],
            }
            cfg[new_latch] = new_latch_block
            header_index = next(
                i for i, block in enumerate(blocks) if block["name"] == header
            )
            blocks.insert(
                header_index + 1, new_latch_block
            )  # insert new latch right after header

            # modify original latch blocks
            for original_latch in original_latches:
                original_latch_block = cfg[original_latch]
                original_latch_block["succs"] = [new_latch]
                # replace the jmp/br to header with jmp/br to new latch
                original_latch_block["instrs"] = [
                    (
                        instr
                        if not (is_jmp(instr) or is_br(instr))
                        else {
                            **instr,
                            "labels": [
                                new_latch if label == header else label
                                for label in instr.get("labels", [])
                            ],
                        }
                    )
                    for instr in original_latch_block["instrs"]
                ]
                latch_block_index = next(
                    i
                    for i, block in enumerate(blocks)
                    if block["name"] == original_latch
                )
                blocks[latch_block_index] = original_latch_block

            # modify header block, remove original latches and replace with new latch
            header_block = cfg[header]
            header_block["preds"] = [
                pred for pred in header_block["preds"] if pred not in original_latches
            ]
            header_block["preds"].append(new_latch)
            header_block_index = next(
                i for i, block in enumerate(blocks) if block["name"] == header
            )
            blocks[header_block_index] = header_block

            # modify loop informations
            new_loop = {
                "header": header,
                "latch": new_latch,
                "blocks": [header, new_latch],
            }
            for loop in shared_loops:
                new_loop["blocks"].extend(
                    [
                        block
                        for block in loop["blocks"]
                        if block not in new_loop["blocks"]
                    ]
                )
            new_loops.append(new_loop)
        else:
            for loop in shared_loops:
                new_loops.append(loop)

    return convert_blocks_to_fn(blocks, fn), new_loops


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        natural_loops = get_natural_loops(fn)
        # print(json.dumps(natural_loops, indent=2))
        new_fn, normalized_loops = normalize_shared_loops(fn, natural_loops)
        fn["instrs"] = new_fn["instrs"]
        # print(json.dumps(new_fn, indent=2))
        # print(json.dumps(normalized_loops, indent=2))
        # natural_loops = get_natural_loops(fn)
        # print(json.dumps(natural_loops, indent=2))
    print(json.dumps(prog, indent=2))
