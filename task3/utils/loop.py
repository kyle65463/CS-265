from copy import deepcopy
from utils.cfg import form_blocks


def is_jmp(instr):
    return "op" in instr and instr["op"] == "jmp"


def is_br(instr):
    return "op" in instr and instr["op"] == "br"


def postorder_rec(cfg, block, visited, result):
    if block["name"] in visited:
        return
    visited.add(block["name"])

    for succ in block["succs"]:
        postorder_rec(cfg, cfg[succ], visited, result)
    result.append(block)


def postorder(cfg, block):
    out = []
    postorder_rec(cfg, block, set(), out)
    return out


def get_dominators(cfg, blocks, strict=False):
    if len(blocks) == 0:
        return {}
    dom = {}
    iter_blocks = reversed(postorder(cfg, blocks[0]))
    while True:
        has_changed = False
        for block in iter_blocks:
            block_name = block["name"]
            block = cfg[block_name]
            original_dom = deepcopy(dom[block_name]) if block_name in dom else None
            dom[block_name] = set()
            dom[block_name].add(block_name)

            pred_dominators = None
            for pred_name in block["preds"]:
                if pred_name == block_name:
                    continue
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
                has_changed = True
        if not has_changed:
            break
    for block in blocks:
        if block["name"] not in dom:
            dom[block["name"]] = set()
        if strict and block["name"] in dom[block["name"]]:
            dom[block["name"]].remove(block["name"])
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
    if current == header:
        return False
    if current == latch:
        return True
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
            "preheader": None,
        }
        for block in blocks:
            if can_reach_latch_without_header(
                cfg, blocks, block["name"], set(), latch, header
            ):
                loop["blocks"].append(block["name"])

        header_block = cfg[header]
        if len(header_block["preds"]) == 2:  # latch and preheader
            loop["preheader"] = next(
                pred for pred in header_block["preds"] if pred != latch
            )

        loops.append(loop)
    return loops
