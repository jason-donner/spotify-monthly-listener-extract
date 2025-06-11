import json
import re
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker  # Add this import
import numpy as np
import seaborn as sns

def parse_listeners(s):
    """Convert '1.2K', '3M', etc. to integer."""
    if isinstance(s, int):
        return s
    s = str(s).replace(',', '').strip()
    match = re.match(r"([\d\.]+)([KM]?)", s)
    if not match:
        return None
    num, suffix = match.groups()
    num = float(num)
    if suffix == "K":
        num *= 1_000
    elif suffix == "M":
        num *= 1_000_000
    return int(num)

with open("src/results/spotify-scraped-listeners-20250610.json", encoding="utf-8") as f:
    data = json.load(f)

listeners = [parse_listeners(d["monthly_listeners"])
             for d in data if "monthly_listeners" in d and d["monthly_listeners"]]
listeners = [l for l in listeners if l is not None]

# Print summary statistics
print(f"Min: {min(listeners):,}")
print(f"Max: {max(listeners):,}")
print(f"Mean: {np.mean(listeners):,.0f}")
print(f"Median: {np.median(listeners):,.0f}")
print(f"90th percentile: {np.percentile(listeners, 90):,.0f}")
print(f"95th percentile: {np.percentile(listeners, 95):,.0f}")
print(f"99th percentile: {np.percentile(listeners, 99):,.0f}")

# Now filter based on your chosen limit, e.g. 90th percentile
limit = int(np.percentile(listeners, 90))
listeners = [l for l in listeners if l <= limit]

plt.style.use("seaborn-v0_8-whitegrid")  # Use a modern, clean style

fig, ax = plt.subplots(figsize=(12, 7))
counts, bins, patches = ax.hist(
    listeners, bins=30, color="#1DB954", edgecolor="black", alpha=0.85, rwidth=0.92
)

# Add value labels on top of each bar
for count, bin_left, bin_right in zip(counts, bins[:-1], bins[1:]):
    if count > 2:  # Only label bars with more than 2 artists
        ax.text(
            (bin_left + bin_right) / 2,
            count + max(counts)*0.01,  # Add a small offset
            f"{int(count)}",
            ha="center",
            va="bottom",
            fontsize=11,
            color="#222",
            rotation=0,
            fontweight="bold"
        )

ax.set_xlabel("Monthly Listeners", fontsize=13, labelpad=12)
ax.set_ylabel("Artist Count", fontsize=13, labelpad=12)
ax.set_title("Distribution of Monthly Listeners for Followed Artists\n(90th Percentile Limit)", fontsize=16, pad=16)

# Format x and y axis with commas
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{int(y):,}"))

plt.tight_layout()
plt.show()

plt.figure(figsize=(12, 3))
sns.boxplot(x=listeners, color="#1DB954", fliersize=5, boxprops=dict(alpha=0.7))
sns.stripplot(x=listeners, color="#222", alpha=0.3, jitter=0.2, size=4)
plt.xlabel("Monthly Listeners")
plt.title("Monthly Listeners Distribution (Box + Strip Plot, 90th Percentile Limit)")
plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
plt.tight_layout()
plt.show()

plt.figure(figsize=(4, 8))
sns.violinplot(
    y=listeners,
    color="#1DB954",
    inner="quartile",
    linewidth=1.2,
    cut=0
)
plt.ylabel("Monthly Listeners", fontsize=13, labelpad=10)
plt.title("Monthly Listeners Distribution (Violin Plot, 90th Percentile Limit)", fontsize=15, pad=12)
plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
plt.tight_layout()
plt.show()

# Violin plot for all artists (no limit)
plt.figure(figsize=(4, 8))
sns.violinplot(
    y=[parse_listeners(d["monthly_listeners"]) for d in data if "monthly_listeners" in d and d["monthly_listeners"] is not None],
    color="#1DB954",
    inner="quartile",
    linewidth=1.2,
    cut=0
)
plt.ylabel("Monthly Listeners", fontsize=13, labelpad=10)
plt.title("Monthly Listeners Distribution (Violin Plot, All Artists)", fontsize=15, pad=12)
plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
plt.tight_layout()
plt.show()