"""EXP-005 visualization: failure taxonomy + consensus-LOC concentration."""
from pathlib import Path
import json, glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

files = sorted(glob.glob("/tmp/cfyow-work/results/EXP-005/devx-*.json"))
data = json.loads(Path(files[-1]).read_text())
VIZ = Path(files[-1]).parent / "viz"
VIZ.mkdir(exist_ok=True)

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# --- left: failure taxonomy — where bugs CAN be caught vs WHERE they were
surfaces = data["failure_taxonomy"]["surfaces_cheap_to_expensive"]
detectable = [data["failure_taxonomy"]["tasks_detectable_per_surface"][s] for s in surfaces]
caught = [data["failure_taxonomy"]["real_incidents_caught_per_surface"][s] for s in surfaces]
y = np.arange(len(surfaces))
axes[0].barh(y + 0.2, detectable, 0.4, label="tasks detectable at this surface", color="#2196f3")
axes[0].barh(y - 0.2, caught, 0.4, label="real incidents caught here", color="#f44336")
axes[0].set_yticks(y)
axes[0].set_yticklabels([s.replace("_", "\n") for s in surfaces], fontsize=8)
axes[0].set_xlabel("count")
axes[0].legend(fontsize=8)
axes[0].set_title("Failure taxonomy: detection capability vs reality\n"
                  "cheap surfaces catch little; the live network catches everything")

# --- right: consensus-sensitive LOC by task, judgment tasks highlighted
tasks = data["tasks"]
names = [f"{t['id']}. {t['name'].split('(')[0].strip()[:28]}" for t in tasks]
locs = [t["consensus_sensitive_lines"] for t in tasks]
colors = ["#e91e63" if t["judgment_added"] else "#90a4ae" for t in tasks]
y2 = np.arange(len(tasks))
axes[1].barh(y2, locs, color=colors)
axes[1].set_yticks(y2)
axes[1].set_yticklabels(names, fontsize=7.5)
axes[1].invert_yaxis()
axes[1].set_xlabel("consensus-sensitive lines of code")
axes[1].set_title(f"Consensus-sensitive LOC concentration\n"
                  f"(pink = judgment-bearing; total {data['total_consensus_sensitive_lines']})")

fig.suptitle("EXP-005 DevX Under Judgment — CFYOW build evidence (8 real incidents, 7 upstream bugs)",
             fontsize=11)
fig.tight_layout()
out = VIZ / "devx-taxonomy.png"
fig.savefig(out, dpi=150)
print("saved", out)
