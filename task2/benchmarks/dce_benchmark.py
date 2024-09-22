import matplotlib.pyplot as plt
import pandas as pd

# Read the data into a DataFrame
data = pd.read_csv("dce_results.csv")

# Convert 'result' column to numeric type
data['result'] = pd.to_numeric(data['result'], errors='coerce')

# Define the desired order of runs
run_order = ["baseline", "old_global_dce", "old_global_dce_with_local_dce", "new_global_dce"]

# Pivot the data to create a matrix suitable for plotting
pivot_data = data.pivot(index="benchmark", columns="run", values="result")

# Reorder the columns according to the desired order
pivot_data = pivot_data[run_order]

# Create the bar plot
ax = pivot_data.plot(kind="bar", figsize=(12, 6), width=0.8)

# Customize the plot
plt.title("Comparison of Different Runs Across Benchmarks")
plt.xlabel("Benchmarks")
plt.ylabel("Result")
plt.legend(title="Runs", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()

# Add value labels on the bars
for container in ax.containers:
    ax.bar_label(container, padding=3)

# Rotate x-axis labels for better readability
plt.xticks(rotation=45, ha="right")

# Show the plot
plt.savefig('dce_benchmark_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
