import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Read the data into a DataFrame
data = pd.read_csv("final_benchmark.csv")

# Convert 'result' column to numeric type, replacing 'incorrect' and 'timeout' with NaN
data["result"] = pd.to_numeric(
    data["result"].replace({"incorrect": float("nan"), "timeout": float("nan")}),
    errors="coerce",
)

# Define the desired order of runs
run_order = ["baseline", "task2", "task3"]

# Pivot the data to create a matrix suitable for plotting
pivot_data = data.pivot(index="benchmark", columns="run", values="result")

# Reorder the columns according to the desired order
pivot_data = pivot_data[run_order]

# Calculate percentage improvement from baseline
for run in ["task2", "task3"]:
    pivot_data[f"{run}_improvement"] = (
        (pivot_data["baseline"] - pivot_data[run]) / pivot_data["baseline"] * 100
    )

# Sort benchmarks by task3 improvement
pivot_data = pivot_data.sort_values("task3_improvement", ascending=False)

# Filter out rows where both task2 and task3 improvements are 0 or NaN
pivot_data = pivot_data[
    (pivot_data["task2_improvement"] != 0) | (pivot_data["task3_improvement"] != 0)
]
pivot_data = pivot_data.dropna(subset=["task2_improvement", "task3_improvement"])

# Split the data into three parts
part_size = len(pivot_data) // 3
pivot_data_1 = pivot_data.iloc[:part_size]
pivot_data_2 = pivot_data.iloc[part_size:2*part_size]
pivot_data_3 = pivot_data.iloc[2*part_size:]

def create_chart(data, title, filename):
    fig, ax = plt.subplots(figsize=(20, 10))
    data[["task2_improvement", "task3_improvement"]].plot(kind="bar", ax=ax, width=0.8)

    plt.title(title)
    plt.xlabel("Benchmarks")
    plt.ylabel("Percentage Improvement (%)")
    plt.legend(
        title="Runs",
        labels=["Task 2", "Task 3"],
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
    )
    plt.tight_layout()

    plt.xticks(rotation=90, ha="right")
    plt.axhline(y=0, color="r", linestyle="-", linewidth=0.5)

    for i, benchmark in enumerate(data.index):
        for j, col in enumerate(["task3_improvement", "task2_improvement"]):
            value = data.loc[benchmark, col]
            if not np.isnan(value) and value != 0:
                plt.text(
                    i + (j - 0.5) * 0.4,
                    value,
                    f"{value:.1f}%",
                    ha="center",
                    va="bottom" if value > 0 else "top",
                    rotation=90,
                    fontsize=8,
                )

    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()

# Create three charts
create_chart(
    pivot_data_1,
    "Percentage Improvement from Baseline Across Benchmarks (Part 1)",
    "final_benchmark_improvement_1.png",
)
create_chart(
    pivot_data_2,
    "Percentage Improvement from Baseline Across Benchmarks (Part 2)",
    "final_benchmark_improvement_2.png",
)
create_chart(
    pivot_data_3,
    "Percentage Improvement from Baseline Across Benchmarks (Part 3)",
    "final_benchmark_improvement_3.png",
)
