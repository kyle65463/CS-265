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
        "legend": f"Optimal ({(metric.upper())})",
        "color": "#15304D",  # Material Blue
    },
    # {
    #     "run": f"inline_autotuner_{metric}_1",
    #     "legend": f"Autotuner ({(metric.upper())}, Round=1)",
    #     "color": "#2E5984",  # Material Green
    # },
    # {
    #     "run": "inline_all",
    #     "legend": "Inline-All",
    #     "color": "#73A5C6",  # Material Amber
    # },
    # {
    #     "run": "inline_fn_size_10",
    #     "legend": "Function-Size (Threshold=10)",
    #     "color": "#BCD2E8",  # Material Purple
    # # },
    # {
    #     "run": "inline_fn_size_20",
    #     "legend": "Inline Fn Size 20",
    #     "color": "#ff99cc",
    # },
    {
        "run": "inline_in_loop",
        "legend": "In-Loop",
        "color": "#2E5984",
    },
    {
        "run": "inline_single_call_site",
        "legend": "Single-Call-Site",
        "color": "#73A5C6",
    },
    {
        "run": "inline_arg_constantness",
        "legend": "Constant-Argument",
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


# Split the data into NUM_PARTS parts
part_size = len(pivot_data) // NUM_PARTS
pivot_data_parts = [
    pivot_data.iloc[i * part_size : (i + 1) * part_size if i < NUM_PARTS - 1 else None]
    for i in range(NUM_PARTS)
]


def create_chart(data, title, filename):
    # Set the default font sizes
    plt.rcParams.update({"font.size": 14})  # Base font size

    _, ax = plt.subplots(figsize=(20, 10))
    improvement_columns = [f"{run['run']}_improvement" for run in COMPARISON_RUNS]
    bar_width = 0.8
    data[improvement_columns].plot(
        kind="bar",
        ax=ax,
        width=bar_width,
        color=[run["color"] for run in COMPARISON_RUNS],
    )

    # Adjust the spacing between groups
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha="right", fontsize=16)

    # Remove the plt.subplots_adjust line and modify tight_layout parameters
    plt.tight_layout(pad=1.0, w_pad=0.1, h_pad=0.1)

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.xlabel("")
    plt.ylabel(
        f"{'Relative Executed Instruction Count Reduction' if metric == 'ic' else 'Relative Program Size Reduction'} (%)",
        fontsize=24,
    )
    plt.legend(
        title="Heuristics",
        labels=[run["legend"] for run in COMPARISON_RUNS],
        loc="best",
        title_fontsize=24,
        fontsize=24,
    )

    plt.yticks(fontsize=18)
    plt.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)

    # Add value labels
    for i, benchmark in enumerate(data.index):
        for j, col in enumerate(improvement_columns):
            value = data.loc[benchmark, col]
            if not np.isnan(value):
                vertical_padding = 0.2
                text_position = (
                    value + vertical_padding if value > 0 else 1.2 + vertical_padding
                )

                plt.text(
                    i
                    + (j - len(improvement_columns) / 2 + 0.5)
                    * (bar_width / len(improvement_columns)),
                    text_position,
                    f"{value:.1f}%",
                    ha="center",
                    va="bottom" if value > 0 else "top",
                    rotation=90,
                    fontsize=18,
                    fontweight=500,
                )

    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()


# Create charts for each part
for i, part_data in enumerate(pivot_data_parts, 1):
    create_chart(
        part_data,
        f"Percentage Improvement from Baseline Across Benchmarks (Part {i} of {NUM_PARTS})",
        f"{metric}_improvement_{2}.png",
    )
