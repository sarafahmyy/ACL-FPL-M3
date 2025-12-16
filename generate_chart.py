import matplotlib.pyplot as plt
import numpy as np

# Data from your report
models = ['Llama-70B', 'GPT-3.5-Turbo', 'GPT-4']
times = [11.64, 11.66, 12.74]       # Average Time per Run (seconds)
costs = [0.00, 0.000578, 0.034606]  # Average Cost per Run ($)

# Create the figure and a set of subplots
fig, ax1 = plt.subplots(figsize=(10, 6))

# Bar width and positions
bar_width = 0.35
index = np.arange(len(models))

# Plot Time (Primary Y-axis) - Blue Bars
bars1 = ax1.bar(index, times, bar_width, label='Avg Time (s)', color='#4e79a7', alpha=0.8)
ax1.set_xlabel('LLM Model', fontsize=12, fontweight='bold')
ax1.set_ylabel('Time (seconds)', color='#4e79a7', fontsize=12, fontweight='bold')
ax1.tick_params(axis='y', labelcolor='#4e79a7')
ax1.set_ylim(0, 15) # Set limit to make bars look proportional

# Create a second Y-axis for Cost
ax2 = ax1.twinx()

# Plot Cost (Secondary Y-axis) - Red Bars
# Shift position by bar_width to place side-by-side
bars2 = ax2.bar(index + bar_width, costs, bar_width, label='Avg Cost ($)', color='#e15759', alpha=0.8)
ax2.set_ylabel('Cost ($)', color='#e15759', fontsize=12, fontweight='bold')
ax2.tick_params(axis='y', labelcolor='#e15759')
ax2.set_ylim(0, 0.04) # Set limit to accommodate GPT-4's higher cost

# Add title and model names on x-axis
plt.title('Performance vs. Cost Analysis: LLM Comparison', fontsize=14, fontweight='bold')
ax1.set_xticks(index + bar_width / 2)
ax1.set_xticklabels(models)

# Add value labels on top of the Time bars
for bar in bars1:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'{height}s',
             ha='center', va='bottom', color='#4e79a7', fontsize=10, fontweight='bold')

# Add value labels on top of the Cost bars
for bar in bars2:
    height = bar.get_height()
    # Format cost to show "Free" for 0 or specific $ amount
    label = 'Free' if height == 0 else f'${height:.4f}'
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             label,
             ha='center', va='bottom', color='#e15759', fontsize=10, fontweight='bold')

# Legend
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines + lines2, labels + labels2, loc='upper left')

# Layout adjustment
plt.tight_layout()

# Save the plot
plt.savefig('comparison_chart.png', dpi=300)
print("Chart saved successfully as 'comparison_chart.png'")
plt.show()