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
    f"inline_optimal_{metric}",
    f"inline_autotuner_{metric}_1",
    "inline_all",
    "inline_fn_size_10",
    "inline_fn_size_20",
    "inline_in_loop",
    "inline_single_call_site",
    "inline_arg_constantness",
]

# Pivot the data to create a matrix suitable for plotting
pivot_data = data.pivot(index="benchmark", columns="run", values="result")

# Calculate percentage improvement from baseline for all comparison runs
for run in COMPARISON_RUNS:
    pivot_data[f"{run}_improvement"] = (
        (pivot_data[BASELINE_RUN] - pivot_data[run]) / pivot_data[BASELINE_RUN] * 100
    )

# Sort benchmarks by the first comparison run's improvement
pivot_data = pivot_data.sort_values(
    f"{COMPARISON_RUNS[0]}_improvement", ascending=False
)

# Filter out rows where all improvements are 0 or NaN
improvement_columns = [f"{run}_improvement" for run in COMPARISON_RUNS]
pivot_data = pivot_data[pivot_data[improvement_columns].any(axis=1)]
pivot_data = pivot_data.dropna(subset=improvement_columns, how="all")


# Split the data into NUM_PARTS parts
part_size = len(pivot_data) // NUM_PARTS
pivot_data_parts = [
    pivot_data.iloc[i * part_size : (i + 1) * part_size if i < NUM_PARTS - 1 else None]
    for i in range(NUM_PARTS)
]


def create_chart(data, title, filename):
    fig, ax = plt.subplots(figsize=(20, 10))
    improvement_columns = [f"{run}_improvement" for run in COMPARISON_RUNS]
    data[improvement_columns].plot(kind="bar", ax=ax, width=0.8)

    plt.title(title)
    plt.xlabel("Benchmarks")
    plt.ylabel("Percentage Improvement (%)")
    plt.legend(
        title="Runs",
        labels=[run.replace("_", " ").title() for run in COMPARISON_RUNS],
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
    )
    plt.tight_layout()

    plt.xticks(rotation=90, ha="right")
    plt.axhline(y=0, color="r", linestyle="-", linewidth=0.5)

    # Add value labels
    for i, benchmark in enumerate(data.index):
        for j, col in enumerate(improvement_columns):
            value = data.loc[benchmark, col]
            if not np.isnan(value) and value != 0:
                plt.text(
                    i
                    + (j - len(improvement_columns) / 2 + 0.5)
                    * (0.8 / len(improvement_columns)),
                    value,
                    f"{value:.1f}%",
                    ha="center",
                    va="bottom" if value > 0 else "top",
                    rotation=90,
                    fontsize=8,
                )

    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()


# Create charts for each part
for i, part_data in enumerate(pivot_data_parts, 1):
    create_chart(
        part_data,
        f"Percentage Improvement from Baseline Across Benchmarks (Part {i} of {NUM_PARTS})",
        f"{metric}_improvement_{i}.png",
    )
