import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the data
data = pd.read_csv("optimal_configs_stats.csv")

# Count the frequency of each num_edges value
edge_counts = data["num_edges"].value_counts().sort_index()

# Create the plot
plt.figure(figsize=(10, 6))
ax = plt.gca()

# Create bar plot
plt.bar(
    edge_counts.index, edge_counts.values, color="#15304D", edgecolor="black", alpha=0.7
)

# Customize the plot
plt.xlabel("Number of Edges in Call Graph", fontsize=14)
plt.ylabel("Number of Benchmarks", fontsize=14)

# Set x-ticks to show all integer values
plt.xticks(range(min(data["num_edges"]), max(data["num_edges"]) + 1), fontsize=12)
plt.yticks(range(max(edge_counts.values) + 1), fontsize=12)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Add grid for better readability
plt.grid(True, axis="y", linestyle="--", alpha=0.7)

# Adjust layout
plt.tight_layout()

# Save the plot
plt.savefig("num_edges_distribution.png", dpi=300, bbox_inches="tight")
plt.close()

# Print some basic statistics
print("\nCall Graph Edges Statistics:")
print(f"Maximum: {data['num_edges'].max()} edges")
print(f"Minimum: {data['num_edges'].min()} edges")
print(f"Average: {data['num_edges'].mean():.1f} edges")
print(f"Median: {data['num_edges'].median()} edges")
