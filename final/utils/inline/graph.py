from typing import Dict, List, Tuple


def form_call_graph(prog: Dict) -> Tuple[Dict, List[Tuple[str, str]]]:
    nodes = {}
    edges = []
    for fn in prog["functions"]:
        name = fn["name"]
        nodes[name] = {
            "name": name,
            "edges": [],
        }
        for instr in fn["instrs"]:
            if "op" in instr and instr["op"] == "call":
                callee = instr["funcs"][0]
                nodes[name]["edges"].append(callee)
    # Deduplicate edges
    for name, data in nodes.items():
        data["edges"] = list(set(data["edges"]))
        for e in data["edges"]:
            edges.append((name, e))

    edges = list(set(edges))
    return nodes, edges
