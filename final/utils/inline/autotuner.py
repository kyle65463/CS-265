from typing import Dict, Tuple
import ast
from pathlib import Path
import csv


csv_path = Path(__file__).parent / "autotuner_configs.csv"


def get_autotuner_program_size_inline_config(
    _: Dict, round: str, name: str
) -> Dict[Tuple[str, str], bool]:
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["program_name"] == name and row["round"] == round:
                return ast.literal_eval(row["best_program_size_config"])
    return {}


def get_autotuner_instruction_count_inline_config(
    _: Dict, round: str, name: str
) -> Dict[Tuple[str, str], bool]:
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["program_name"] == name and row["round"] == round:
                return ast.literal_eval(row["best_executed_instr_count_config"])
    return {}
