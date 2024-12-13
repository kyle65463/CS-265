import time
from typing import Dict, List
import json
import glob
import os
import subprocess

from benchmark import count_executed_instructions, count_program_size
from utils.inline.graph import find_recursive_functions, form_call_graph
from inline import inline


def read_bril_programs(path: str) -> List[Dict]:
    progs = []
    for bril_file in glob.glob(os.path.join(path, "**/*.bril"), recursive=True):
        try:
            # Read the file and look for ARGS in any line
            with open(bril_file) as f:
                lines = f.readlines()
                args = ""
                for line in lines:
                    if line.strip().startswith("# ARGS:"):
                        args = line.replace("# ARGS:", "").strip()
                        break

                input = "".join(lines)

            # Run bril2json on the .bril file and capture its output
            result = subprocess.run(
                ["bril2json"],
                input=input,
                capture_output=True,
                text=True,
                check=True,
            )
            # Parse the JSON output
            bril_data = json.loads(result.stdout)
            bril_data["args"] = args.split()
            bril_data["name"] = os.path.basename(bril_file)
            progs.append(bril_data)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Warning: Skipping {bril_file} - {str(e)}")
    return progs


def generate_all_possible_configs(prog: Dict) -> List[Dict]:
    _, edges = form_call_graph(prog)

    # Find recursive functions
    recursive = find_recursive_functions(edges)

    # Filter out recursive edges
    non_recursive_edges = [
        (src, dest)
        for src, dest in edges
        if src not in recursive or dest not in recursive
    ]

    # Safety check - limit maximum edges to prevent memory issues
    MAX_EDGES = 12
    if len(non_recursive_edges) > MAX_EDGES:
        print(f"Skipping")
        print(f"#edges: {len(non_recursive_edges)}")
        raise ValueError(
            f"Too many edges ({len(non_recursive_edges)}) in call graph. Maximum supported is {MAX_EDGES} "
            f"to prevent memory issues (would generate {2**len(non_recursive_edges)} configurations)"
        )

    # Generate all possible combinations using binary numbers
    num_configs = 2 ** len(non_recursive_edges)
    configs = []

    for i in range(num_configs):
        config = {}
        # Convert number to binary and pad with zeros
        binary = format(i, f"0{len(non_recursive_edges)}b")

        # Create config dictionary where each edge maps to True/False
        for edge_idx, edge in enumerate(non_recursive_edges):
            caller, callee = edge
            config[(caller, callee)] = binary[edge_idx] == "1"

        # Add recursive edges as False
        for src, dest in edges:
            if src in recursive and dest in recursive:
                config[(src, dest)] = False

        configs.append(config)

    return configs


def run_pipeline(cmds, input, timeout):
    """Execute a pipeline of shell commands.

    Send the given input (text) string into the first command, then pipe
    the output of each command into the next command in the sequence.
    Collect and return the stdout and stderr from the final command.
    """
    procs = []
    for cmd in cmds:
        last = len(procs) == len(cmds) - 1
        proc = subprocess.Popen(
            cmd,
            shell=True,
            text=True,
            stdin=procs[-1].stdout if procs else subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if last else subprocess.DEVNULL,
        )
        procs.append(proc)

    try:
        procs[0].stdin.write(input)
        procs[0].stdin.close()
        stdout, _ = procs[-1].communicate(timeout=timeout)
        return json.loads(stdout)
    except Exception as e:
        raise e
    finally:
        for proc in procs:
            proc.kill()


pipeline = [
    "python idce.py",
    "python constant.py",
    "python lvn.py",
    "python liveness_dce.py",
]


if __name__ == "__main__":
    # Add CSV header
    csv_file = "utils/inline/optimal_configs.csv"
    with open(csv_file, "w") as f:
        f.write(
            "program_name,best_program_size,best_executed_instructions,best_program_size_config,best_executed_instr_count_config\n"
        )

    progs = read_bril_programs("../benchmarks")
    for prog in progs:
        try:
            time_start = time.time()
            configs = generate_all_possible_configs(prog)
            print(f"Program: {prog['name']}")
            print(f"Number of configs: {len(configs)}")
            best_program_size = float("inf")
            best_program_size_config = None
            best_executed_instr_count = float("inf")
            best_executed_instr_count_config = None
            for i, config in enumerate(configs):
                print(f"Config {i+1} of {len(configs)}")
                prog = inline(prog, config)
                processed_prog = run_pipeline(pipeline, json.dumps(prog), 15)
                executed_instr_count = count_executed_instructions(processed_prog)
                program_size = count_program_size(prog)
                if program_size < best_program_size:
                    best_program_size = program_size
                    best_program_size_config = config
                if executed_instr_count < best_executed_instr_count:
                    best_executed_instr_count = executed_instr_count
                    best_executed_instr_count_config = config

            with open(csv_file, "a") as f:
                f.write(
                    f'{prog["name"]},{best_program_size},{best_executed_instr_count},"{best_program_size_config}","{best_executed_instr_count_config}"\n'
                )
            print()

        except Exception as e:
            with open(csv_file, "a") as f:
                f.write(f'{prog["name"]},-1,-1,"",""\n')
            print(f"Error: {e}")
            print("Skipping")