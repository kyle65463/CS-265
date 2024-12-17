import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the data
data = pd.read_csv("optimal_configs_stats.csv")

# Calculate percentages
data["program_size_percentage"] = (
    data["best_program_size_config_inline_count"] / data["num_edges"]
) * 100
data["instruction_count_percentage"] = (
    data["best_executed_instructions_config_inline_count"] / data["num_edges"]
) * 100

# Print statistics
print("\nProgram Size Percentage Statistics:")
print(f"Maximum: {data['program_size_percentage'].max():.1f}%")
print(f"Minimum: {data['program_size_percentage'].min():.1f}%")
print(f"Average: {data['program_size_percentage'].mean():.1f}%")

print("\nInstruction Count Percentage Statistics:")
print(f"Maximum: {data['instruction_count_percentage'].max():.1f}%")
print(f"Minimum: {data['instruction_count_percentage'].min():.1f}%")
print(f"Average: {data['instruction_count_percentage'].mean():.1f}%")

# Sort by program size percentage
data = data.sort_values("program_size_percentage", ascending=False)

# Create the plot
plt.figure(figsize=(20, 10))
ax = plt.gca()

# Set bar width
bar_width = 0.35

# Create bars
x = np.arange(len(data))
program_size_bars = plt.bar(
    x - bar_width / 2,
    data["program_size_percentage"],
    bar_width,
    label="Program Size",
    color="#15304D",
)
instruction_count_bars = plt.bar(
    x + bar_width / 2,
    data["instruction_count_percentage"],
    bar_width,
    label="Instruction Count",
    color="#BCD2E8",
)

# Customize the plot
plt.xlabel("")
plt.ylabel("Percentage of Edges Inlined (%)", fontsize=24)
plt.xticks(x, data["program_name"], rotation=90, ha="right", fontsize=16)
plt.yticks(fontsize=18)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Add legend
plt.legend(fontsize=22, loc="best")


# Add value labels
def add_value_labels(bars):
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 1,
            f"{height:.1f}%",
            ha="center",
            va="bottom",
            rotation=90,
            fontsize=18,
            fontweight=500,
        )


add_value_labels(program_size_bars)
add_value_labels(instruction_count_bars)

# Add horizontal line at y=0
plt.axhline(y=0, color="r", linestyle="-", linewidth=0.5)

# Adjust layout
plt.tight_layout(pad=1.0)

# Save the plot
plt.savefig("optimal_configs_stats_plot.png", dpi=300, bbox_inches="tight")
plt.close()
