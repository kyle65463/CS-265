import json
import subprocess
import sys
from typing import Dict


def run_pipeline(input):
    """Execute a pipeline of shell commands.

    Send the given input (text) string into the first command, then pipe
    the output of each command into the next command in the sequence.
    Collect and return the stdout and stderr from the final command.
    """
    cmds = [
        "python idce.py",
        "python constant.py",
        "python lvn.py",
        "python liveness_dce.py",
    ]
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
        stdout, _ = procs[-1].communicate(timeout=15)
        return json.loads(stdout)
    except Exception as e:
        raise e
    finally:
        for proc in procs:
            proc.kill()


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
