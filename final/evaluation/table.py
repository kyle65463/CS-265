import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Read the data into a DataFrame
if len(sys.argv) != 2:
    print("Usage: python final_benchmark.py <filename>")
    sys.exit(1)

metric = sys.argv[1]

data = pd.read_csv(f"{metric}.csv")

# Convert 'result' column to numeric type, replacing 'incorrect' and 'timeout' with NaN
data["result"] = pd.to_numeric(
    data["result"].replace({"incorrect": float("nan"), "timeout": float("nan")}),
    errors="coerce",
)

# Define the baseline and comparison runs
NUM_PARTS = 1
BASELINE_RUN = "task2"
COMPARISON_RUNS = [
    {
        "run": f"inline_optimal_{metric}",
        "legend": "Optimal",
        "color": "#15304D",  # Material Blue
    },
    # {
    #     "run": f"inline_autotuner_{metric}_1",
    #     "legend": "Autotuner",
    #     "color": "#2E5984",  # Material Green
    # },
    # {
    #     "run": "inline_all",
    #     "legend": "All",
    #     "color": "#73A5C6",  # Material Amber
    # },
    # {
    #     "run": "inline_fn_size_10",
    #     "legend": "Function Size < 10",
    #     "color": "#BCD2E8",  # Material Purple
    # },
    # {
    #     "run": "inline_fn_size_20",
    #     "legend": "Inline Fn Size 20",
    #     "color": "#ff99cc",
    # },
    {
        "run": "inline_in_loop",
        "legend": "In Loop",
        "color": "#2E5984",
    },
    {
        "run": "inline_single_call_site",
        "legend": "Single Call Site",
        "color": "#73A5C6",
    },
    {
        "run": "inline_arg_constantness",
        "legend": "Constant Arg Count >= 1",
        "color": "#BCD2E8",
    },
]

# Pivot the data to create a matrix suitable for plotting
pivot_data = data.pivot(index="benchmark", columns="run", values="result")

# Calculate percentage improvement from baseline for all comparison runs
for run in COMPARISON_RUNS:
    pivot_data[f"{run['run']}_improvement"] = (
        (pivot_data[BASELINE_RUN] - pivot_data[run["run"]])
        / pivot_data[BASELINE_RUN]
        * 100
    )

# Sort benchmarks by the first comparison run's improvement
pivot_data = pivot_data.sort_values(
    f"{COMPARISON_RUNS[0]['run']}_improvement", ascending=False
)

# Filter out rows where all improvements are 0 or NaN
improvement_columns = [f"{run['run']}_improvement" for run in COMPARISON_RUNS]
pivot_data = pivot_data[pivot_data[improvement_columns].any(axis=1)]
pivot_data = pivot_data.dropna(subset=improvement_columns, how="all")

# After calculating improvements but before the plotting code
for run in COMPARISON_RUNS:
    improvement_col = f"{run['run']}_improvement"
    improvements = pivot_data[improvement_col].dropna()

    max_improvement = improvements.max()
    max_benchmark = improvements.idxmax()

    min_improvement = improvements.min()
    min_benchmark = improvements.idxmin()

    avg_improvement = improvements.mean()

    print(f"\nStats for {run['legend']}:")
    print(f"Max improvement: {max_improvement:.2f}% ({max_benchmark})")
    print(f"Min improvement: {min_improvement:.2f}% ({min_benchmark})")
    print(f"Average improvement: {avg_improvement:.2f}%")

# Split the data into NUM_PARTS parts
part_size = len(pivot_data) // NUM_PARTS
pivot_data_parts = [
    pivot_data.iloc[i * part_size : (i + 1) * part_size if i < NUM_PARTS - 1 else None]
    for i in range(NUM_PARTS)
]
