import json
import sys
from copy import deepcopy
from utils.loop import get_natural_loops, is_br, is_jmp
from utils.cfg import convert_blocks_to_fn, form_blocks


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


def insert_preheaders(fn, loops):
    cfg, blocks = form_blocks(fn)
    cfg, blocks = deepcopy(cfg), deepcopy(blocks)

    for loop in loops:
        header = loop["header"]
        header_block = cfg[header]

        # insert preheader block
        preheader = f"{header}_preheader"
        preheader_block = {
            "name": preheader,
            "instrs": [
                {
                    "label": preheader,
                },
                {
                    "op": "jmp",
                    "args": [],
                    "labels": [header],
                },
            ],
            "preds": [
                pred for pred in header_block["preds"] if pred not in loop["blocks"]
            ],
            "succs": [header],
        }
        cfg[preheader] = preheader_block
        header_index = next(
            i for i, block in enumerate(blocks) if block["name"] == header
        )
        blocks.insert(header_index, preheader_block)

        # modify header block
        header_preds = header_block["preds"]
        header_block["preds"] = [preheader]
        header_index = next(
            i for i, block in enumerate(blocks) if block["name"] == header
        )
        blocks[header_index] = header_block

        # modify original header pred blocks
        for pred_name in header_preds:
            if pred_name in loop["blocks"]:
                continue
            pred_block = cfg[pred_name]
            pred_block["instrs"] = [
                (
                    instr
                    if not (is_jmp(instr) or is_br(instr))
                    else {
                        **instr,
                        "labels": [
                            preheader if label == header else label
                            for label in instr.get("labels", [])
                        ],
                    }
                )
                for instr in pred_block["instrs"]
            ]
            pred_block["succs"] = [
                preheader if succ == header else succ for succ in pred_block["succs"]
            ]
            pred_index = next(
                i for i, block in enumerate(blocks) if block["name"] == pred_name
            )
            blocks[pred_index] = pred_block

    return convert_blocks_to_fn(blocks, fn)


def is_deterministic(instr):
    # This is a simplified check. In a real compiler, you'd need a more comprehensive list.
    non_deterministic_ops = [
        "jmp",
        "br",
        "call",
        "ret",
        "print",
        "nop",
        "store",
        "free",
        "speculate",
        "commit",
        "guard",
    ]
    return "op" in instr and instr["op"] and instr["op"] not in non_deterministic_ops


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        natural_loops = get_natural_loops(fn)
        new_fn, normalized_loops = normalize_shared_loops(fn, natural_loops)
        fn["instrs"] = new_fn["instrs"]

        new_fn = insert_preheaders(new_fn, normalized_loops)
        fn["instrs"] = new_fn["instrs"]
    print(json.dumps(prog, indent=2))
