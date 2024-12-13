import json
import subprocess
import sys
from typing import Dict


def count_program_size(prog: Dict) -> int:
    count = 0
    for func in prog["functions"]:
        count += len(func["instrs"])
    return count


def count_executed_instructions(prog: Dict) -> int:
    try:
        # Run brili and capture output
        cmd = ["brili", "-p"] + prog["args"]
        result = subprocess.run(
            cmd, input=json.dumps(prog), capture_output=True, text=True, check=True
        )
        output = result.stderr
        instr_count = output.split("total_dyn_inst: ")[1]
        return int(instr_count)

    except subprocess.CalledProcessError as e:
        print(f"Error running brili: {e}")
        return 0


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    size = count_program_size(prog)
    print(f"program_size: {size}", file=sys.stderr)
