import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Read the data into a DataFrame
data = pd.read_csv("benchmark.csv")

# Convert 'result' column to numeric type, replacing 'incorrect' and 'timeout' with NaN
data["result"] = pd.to_numeric(
    data["result"].replace({"incorrect": float("nan"), "timeout": float("nan")}),
    errors="coerce",
)

# Define the desired order of runs
run_order = ["baseline", "task2", "task4"]

# Pivot the data to create a matrix suitable for plotting
pivot_data = data.pivot(index="benchmark", columns="run", values="result")

# Reorder the columns according to the desired order
pivot_data = pivot_data[run_order]

# Calculate percentage improvement from baseline
for run in ["task2", "task4"]:
    pivot_data[f"{run}_improvement"] = (
        (pivot_data["baseline"] - pivot_data[run]) / pivot_data["baseline"] * 100
    )

# Sort benchmarks by task4 improvement
pivot_data = pivot_data.sort_values("task4_improvement", ascending=False)

# Remove the filtering of rows where improvements are 0 or NaN to show all benchmarks
# pivot_data = pivot_data[
#     (pivot_data["task2_improvement"] != 0) | (pivot_data["task4_improvement"] != 0)
# ]
# pivot_data = pivot_data.dropna(subset=["task2_improvement", "task4_improvement"])

# Create the chart
fig, ax = plt.subplots(figsize=(20, 10))
pivot_data[["task2_improvement", "task4_improvement"]].plot(
    kind="bar", ax=ax, width=0.8
)

plt.title("Percentage Improvement from Baseline Across Benchmarks")
plt.xlabel("Benchmarks")
plt.ylabel("Percentage Improvement (%)")
plt.legend(
    title="Runs",
    labels=["Task 2", "Task 4"],
    bbox_to_anchor=(1.05, 1),
    loc="upper left",
)
plt.tight_layout()

plt.xticks(rotation=90, ha="right")
plt.axhline(y=0, color="r", linestyle="-", linewidth=0.5)

for i, benchmark in enumerate(pivot_data.index):
    for j, col in enumerate(["task4_improvement", "task2_improvement"]):
        value = pivot_data.loc[benchmark, col]
        if not np.isnan(value):  # Show all values, including 0
            plt.text(
                i + (j - 0.5) * 0.4,
                value,
                f"{value:.1f}%",
                ha="center",
                va="bottom" if value > 0 else "top",
                rotation=90,
                fontsize=8,
            )

plt.savefig("benchmark_improvement.png", dpi=300, bbox_inches="tight")
plt.close()
