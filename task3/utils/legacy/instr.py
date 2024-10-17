def is_side_effect_free(instr):
    side_effect_ops = {
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
    }
    return "op" in instr and instr["op"] not in side_effect_ops


def get_args_set(instr):
    if "args" in instr:
        return set(instr["args"])
    return set()

def get_args_list(instr):
    if "args" in instr:
        return list(instr["args"])
    return []


def get_dest(instr):
    if "dest" in instr:
        return instr["dest"]
    return None


def is_commutative(instr):
    return "op" in instr and instr["op"] in {"add", "mul"}
