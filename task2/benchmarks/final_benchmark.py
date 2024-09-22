import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Read the data into a DataFrame
data = pd.read_csv("final_full.csv")

# Convert 'result' column to numeric type, replacing 'incorrect' and 'timeout' with NaN
data['result'] = pd.to_numeric(data['result'].replace({'incorrect': float('nan'), 'timeout': float('nan')}), errors='coerce')

# Define the desired order of runs
run_order = ["baseline", "task1", "task2"]

# Pivot the data to create a matrix suitable for plotting
pivot_data = data.pivot(index="benchmark", columns="run", values="result")

# Reorder the columns according to the desired order
pivot_data = pivot_data[run_order]

# Calculate percentage improvement from baseline
for run in ["task1", "task2"]:
    pivot_data[f"{run}_improvement"] = (pivot_data["baseline"] - pivot_data[run]) / pivot_data["baseline"] * 100

# Sort benchmarks by task2 improvement
pivot_data = pivot_data.sort_values("task2_improvement", ascending=False)

# Filter out rows where both task1 and task2 improvements are 0 or NaN
pivot_data = pivot_data[(pivot_data["task1_improvement"] != 0) | (pivot_data["task2_improvement"] != 0)]
pivot_data = pivot_data.dropna(subset=["task1_improvement", "task2_improvement"])

# Create the bar plot for percentage improvements
fig, ax = plt.subplots(figsize=(20, 10))
pivot_data[["task1_improvement", "task2_improvement"]].plot(kind="bar", ax=ax, width=0.8)

# Customize the plot
plt.title("Percentage Improvement from Baseline Across Benchmarks")
plt.xlabel("Benchmarks")
plt.ylabel("Percentage Improvement (%)")
plt.legend(title="Runs", labels=["Task 1", "Task 2"], bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()

# Rotate x-axis labels for better readability
plt.xticks(rotation=90, ha="right")

# Add a horizontal line at y=0
plt.axhline(y=0, color='r', linestyle='-', linewidth=0.5)

# Add value labels on the bars
for i, benchmark in enumerate(pivot_data.index):
    for j, col in enumerate(["task1_improvement", "task2_improvement"]):
        value = pivot_data.loc[benchmark, col]
        if not np.isnan(value) and value != 0:
            plt.text(i + (j-0.5)*0.4, value, f'{value:.1f}%', 
                     ha='center', va='bottom' if value > 0 else 'top', rotation=90, fontsize=8)

# Show the plot
plt.savefig('final_benchmark_improvement.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot for final_lvn.csv
lvn_data = pd.read_csv("final_lvn.csv")
lvn_data['result'] = pd.to_numeric(lvn_data['result'], errors='coerce')

lvn_pivot_data = lvn_data.pivot(index="benchmark", columns="run", values="result")
lvn_pivot_data = lvn_pivot_data[run_order]

lvn_ax = lvn_pivot_data.plot(kind="bar", figsize=(12, 6), width=0.8)

plt.title("Comparison of Different Runs Across Benchmarks (LVN)")
plt.xlabel("Benchmarks")
plt.ylabel("Result")
plt.legend(title="Runs", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()

for container in lvn_ax.containers:
    lvn_ax.bar_label(container, padding=3)

plt.xticks(rotation=45, ha="right")

plt.savefig('final_lvn_benchmark_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
