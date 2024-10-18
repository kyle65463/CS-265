import json
import sys


TERMINATORS = ["jmp", "br", "ret"]


def form_blocks(func):
    blocks = []
    cur_block = []

    for instr in func["instrs"]:
        if "label" in instr:
            if cur_block:
                blocks.append(cur_block)
            cur_block = [instr]
        else:
            cur_block.append(instr)
            if "op" in instr and instr["op"] in TERMINATORS:
                blocks.append(cur_block)
                cur_block = []

    if cur_block:
        blocks.append(cur_block)

    name2block = {}
    for i, block in enumerate(blocks):
        if "label" in block[0]:
            name = block[0]["label"]
        else:
            name = f"b{i}"
            block.insert(0, {"label": name})
        name2block[name] = block

    cfg = {}
    for i, (name, block) in enumerate(name2block.items()):
        if block:
            last = block[-1]
            if "op" in last and last["op"] in ["jmp", "br"]:
                succ = last["labels"]
            elif "op" in last and last["op"] == "ret":
                succ = []
            else:
                succ = (
                    [list(name2block.keys())[i + 1]] if i < len(name2block) - 1 else []
                )
        else:
            succ = [list(name2block.keys())[i + 1]] if i < len(name2block) - 1 else []

        cfg[name] = {"name": name, "instrs": block, "succs": succ, "preds": []}

    for bb_name, bb_data in cfg.items():
        for pred_name, pred_data in cfg.items():
            if bb_name in pred_data["succs"]:
                bb_data["preds"].append(pred_name)

    blocks = [block for _, block in cfg.items()]

    return cfg, blocks


def convert_blocks_to_fn(blocks, original_fn):
    combined_instrs = []
    for block in blocks:
        combined_instrs.extend(block["instrs"])

    return {
        **original_fn,
        "instrs": combined_instrs,
    }


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        cfg = form_blocks(fn)
        print(json.dumps(cfg, indent=2))
