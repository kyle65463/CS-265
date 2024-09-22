from utils.form_blocks import form_blocks


def print_df(blocks, ins, outs):
    for block in blocks:
        id = block["id"]
        print(block["label"])
        print(ins[id])
        print(outs[id])
        print()

def forward_df(fn, f, meet, initial_value={}, print_result=False):
    blocks = form_blocks(fn)

    q, ins, outs = set(), [], []
    for i in range(len(blocks)):
        q.add(i)
        ins.append(initial_value)
        outs.append(initial_value)

    while len(q) > 0:
        id = q.pop()
        block = blocks[id]
        ins[id] = meet([outs[p] for p in block["predecessors"]])
        original_outs = outs[id].copy()
        outs[id] = f(block, ins[id])
        if outs[id] != original_outs:
            for succ in block["successors"]:
                q.add(succ)

    if print_result:
        print_df(blocks, ins, outs)


def backward_df(fn, f, meet, initial_value={}, print_result=False):
    blocks = form_blocks(fn)

    q, ins, outs = set(), [], []
    for i in range(len(blocks)):
        q.add(len(blocks) - 1 - i)
        ins.append(initial_value)
        outs.append(initial_value)

    while len(q) > 0:
        id = q.pop()
        block = blocks[id]
        outs[id] = meet([ins[p] for p in block["successors"]])
        original_ins = ins[id].copy()
        ins[id] = f(block, outs[id])
        if ins[id] != original_ins:
            for pred in block["predecessors"]:
                q.add(pred)

    if print_result:
        print_df(blocks, ins, outs)
