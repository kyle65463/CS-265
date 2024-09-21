import uuid


TERMINATORS = {"br", "jmp", "ret"}


def form_blocks(fn):
    blocks = []
    cur_instrs = []
    label = str(uuid.uuid4())
    for instr in fn["instrs"]:
        if "label" in instr:
            if len(cur_instrs) > 0:
                blocks.append(
                    {
                        "label": label,
                        "instrs": cur_instrs,
                    }
                )
            # Start a new block
            cur_instrs = [instr]
            label = instr["label"]
        elif "op" in instr:
            cur_instrs.append(instr)
            if instr["op"] in TERMINATORS:
                blocks.append(
                    {
                        "label": label,
                        "instrs": cur_instrs,
                    }
                )
                cur_instrs = []
    if len(cur_instrs) > 0:
        blocks.append(
            {
                "label": label,
                "instrs": cur_instrs,
            }
        )
    
    for i, block in enumerate(blocks):
        block["id"] = i
        block['predecessors'] = []
        block['successors'] = []

    for i, block in enumerate(blocks):
        last_instr = block['instrs'][-1]
        if 'op' in last_instr:
            if last_instr['op'] == 'jmp':
                target_label = last_instr['labels'][0]
                for j, target_block in enumerate(blocks):
                    if target_block['label'] == target_label:
                        block['successors'].append(j)
                        target_block['predecessors'].append(i)
                        break
            elif last_instr['op'] == 'br':
                for label in last_instr['labels']:
                    for j, target_block in enumerate(blocks):
                        if target_block['label'] == label:
                            block['successors'].append(j)
                            target_block['predecessors'].append(i)
                            break
            elif last_instr['op'] != 'ret':
                if i + 1 < len(blocks):
                    block['successors'].append(i + 1)
                    blocks[i + 1]['predecessors'].append(i)
        elif i + 1 < len(blocks):
            block['successors'].append(i + 1)
            blocks[i + 1]['predecessors'].append(i)

    return blocks