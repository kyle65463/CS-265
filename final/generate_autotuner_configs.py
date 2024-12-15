from copy import deepcopy
import sys
from typing import Dict
import json

from benchmark import count_executed_instructions, count_program_size, run_pipeline
from generate_optimal_configs import read_bril_programs
from utils.inline.graph import find_recursive_functions, form_call_graph
from inline import inline


def autotuner(
    prog: Dict,
    measure_fn,
    initial_config=None,
) -> Dict:
    _, edges = form_call_graph(prog)
    recursive = find_recursive_functions(edges)

    if initial_config == None:
        initial_config = {
            edge: False
            for edge in edges
            if edge[0] not in recursive or edge[1] not in recursive
        }
    initial_value = measure_fn(
        run_pipeline(json.dumps(inline(deepcopy(prog), initial_config)))
    )
    print(f"Initial config: {initial_config}")
    print(f"Initial value: {initial_value}")

    best_config = {}
    for edge in edges:
        if edge[0] in recursive and edge[1] in recursive:
            continue

        config = deepcopy(initial_config)
        config[edge] = True
        processed_prog = inline(deepcopy(prog), config)
        processed_prog = run_pipeline(json.dumps(processed_prog))
        value = measure_fn(run_pipeline(json.dumps(processed_prog)))

        if value <= initial_value:
            best_config[edge] = True
        else:
            best_config[edge] = False

    return best_config


if __name__ == "__main__":
    # Add CSV header
    total_round = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    csv_file = "utils/inline/autotuner_configs.csv"
    with open(csv_file, "w") as f:
        f.write(
            "program_name,round,best_program_size,best_executed_instructions,best_program_size_config,best_executed_instr_count_config\n"
        )

    progs = read_bril_programs("../benchmarks")
    for raw_prog in progs:
        try:
            print(f"Program: {raw_prog['name']}")
            current_best_program_size_config = None
            current_best_executed_instr_count_config = None
            for round in range(1, total_round + 1):
                print(f"Round {round} of {total_round}")
                prog = deepcopy(raw_prog)
                best_program_size_config = autotuner(
                    prog, count_program_size, current_best_program_size_config
                )
                best_executed_instr_count_config = autotuner(
                    prog,
                    count_executed_instructions,
                    current_best_executed_instr_count_config,
                )
                best_program_size = count_program_size(
                    run_pipeline(json.dumps(inline(prog, best_program_size_config)))
                )
                best_executed_instr_count = count_executed_instructions(
                    run_pipeline(
                        json.dumps(inline(prog, best_executed_instr_count_config))
                    )
                )
                print(f"Best program size: {best_program_size}")
                print(f"Best program size config: {best_program_size_config}")
                print(f"Best executed instructions: {best_executed_instr_count}")
                print(
                    f"Best executed instructions config: {best_executed_instr_count_config}"
                )
                with open(csv_file, "a") as f:
                    f.write(
                        f'{prog["name"]},{round},{best_program_size},{best_executed_instr_count},"{best_program_size_config}","{best_executed_instr_count_config}"\n'
                    )
                current_best_program_size_config = best_program_size_config
                current_best_executed_instr_count_config = (
                    best_executed_instr_count_config
                )
                print()
            print()

        except Exception as e:
            with open(csv_file, "a") as f:
                f.write(f'{raw_prog["name"]},-1,-1,"",""\n')
            print(f"Error: {e}")
            print("Skipping")
