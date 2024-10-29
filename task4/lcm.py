import json
import sys
from utils.legacy.instr import is_commutative
from utils.legacy.dataflow import backward_df, forward_df
from utils.legacy.form_blocks import form_blocks


def union(succ_ins):
    if len(succ_ins) == 0:
        return set()
    return succ_ins[0].union(*succ_ins[1:])


def inter(succ_ins):
    if len(succ_ins) == 0:
        return set()
    return succ_ins[0].intersection(*succ_ins[1:])


def get_expr(instr):
    if "op" in instr and instr["op"] == "const":
        return None
        return f"const {instr['value']}"
    elif "args" not in instr or len(instr["args"]) != 2:
        return None
    if is_commutative(instr):
        instr["args"] = sorted(instr["args"])
    return instr["op"] + " " + " ".join([str(x) for x in instr["args"]])


def get_used_exprs(block):
    used = set()
    for instr in block["instrs"]:
        expr = get_expr(instr)
        if expr is not None:
            used.add(expr)
    return used


def get_killed_dests(block):
    killed_dest = set()
    for instr in block["instrs"]:
        if "dest" in instr:
            killed_dest.add(instr["dest"])
    return killed_dest


def get_killed_exprs(original_exprs, killed_dests):
    killed_exprs = set()
    for expr in original_exprs:
        for killed_dest in killed_dests:
            if killed_dest in expr.split():
                killed_exprs.add(expr)
    return killed_exprs


def anticipated_expr_f(block, x):
    used = get_used_exprs(block)
    killed_dests = get_killed_dests(block)
    killed_exprs = get_killed_exprs(x, killed_dests)
    result = used.union(x.copy() - killed_exprs)
    return result


def available_expr_f(block, x):
    block["earliest"] = block["anticipated"]["in"] - x
    killed_dests = get_killed_dests(block)
    killed_exprs = get_killed_exprs(
        x.copy().union(block["anticipated"]["in"]), killed_dests
    )
    result = x.copy().union(block["anticipated"]["in"]) - killed_exprs
    return result


def postponable_expr_f(block, x):
    used = get_used_exprs(block)
    result = x.copy().union(block["earliest"]) - used
    return result


def liveness_expr_f(block, x):
    used = get_used_exprs(block)
    result = used.union(x.copy()) - block["latest"]
    return result


def calculate_earliest(blocks):
    for block in blocks:
        block["earliest"] = block["anticipated"]["in"] - block["available"]["in"]


def calculate_latest(blocks):
    for block in blocks:
        # Calculate the intersection over all successors
        if block["successors"]:
            succ_exprs = set()
            for s in block["successors"]:
                succ_set = blocks[s]["earliest"].union(blocks[s]["postponable"]["in"])
                if not succ_exprs:
                    succ_exprs = succ_set
                else:
                    succ_exprs = succ_exprs.intersection(succ_set)
        else:
            succ_exprs = set()

        current_exprs = block["earliest"].union(block["postponable"]["in"])
        negated_succ_exprs = current_exprs.difference(succ_exprs)
        # Get used expressions (EUse_b) in the current block
        used_exprs = get_used_exprs(block)

        latest = (block["earliest"].union(block["postponable"]["in"])).intersection(
            used_exprs.union(negated_succ_exprs)
        )
        block["latest"] = latest


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        print("ANTICIPATED")
        blocks = form_blocks(fn, add_empty_blocks=True)
        blocks = backward_df(
            anticipated_expr_f,
            inter,
            name="anticipated",
            blocks=blocks,
            initial_value=set(),
            print_result=True,
        )
        print()
        print("AVAILABLE")
        blocks = forward_df(
            available_expr_f,
            inter,
            name="available",
            blocks=blocks,
            initial_value=set(),
            print_result=True,
        )

        print("EARLIEST")
        calculate_earliest(blocks)
        for block in blocks:
            print(block["label"])
            print(block["earliest"])
            print()

        print("POSTPONABLE")
        blocks = forward_df(
            postponable_expr_f,
            inter,
            name="postponable",
            blocks=blocks,
            initial_value=set(),
            print_result=True,
        )

        print("LATEST")
        calculate_latest(blocks)
        for block in blocks:
            print(block["label"])
            print(block["latest"])
            print()
