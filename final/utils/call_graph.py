import json
import sys


def form_call_graph(prog):
    nodes = {}
    edges = []
    for fn in prog["functions"]:
        name = fn["name"]
        nodes[name] = {
            "name": name,
            "edges": [],
        }
        for instr in fn["instrs"]:
            # add edges
            if "op" in instr and instr["op"] == "call":
                nodes[name]["edges"].append(instr["funcs"][0])
                edges.append((name, instr["funcs"][0]))
            
            # remove duplicates
            nodes[name]["edges"] = list(set(nodes[name]["edges"]))
    # remove duplicates
    edges = list(set(edges))
    return nodes, edges

if __name__ == "__main__":
    prog = json.load(sys.stdin)
    nodes, edges = form_call_graph(prog)
    print(json.dumps(nodes, indent=2))
    print(json.dumps(edges, indent=2))
