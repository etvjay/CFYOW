"""EXP-004 visualization: autonomy budget comparison."""
from pathlib import Path
import json, glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

files = sorted(glob.glob("/tmp/cfyow-work/results/EXP-004/autonomy-budget-*.json"))
data = json.loads(Path(files[-1]).read_text())
wf = data["workflows"]

names = list(wf.keys())
labels = ["Monolithic\n(one contract)", "Chained contracts\n(IC-per-step)"]
metrics = {
    "transitions_total": [wf[n]["budget"]["transitions_total"] for n in names],
    "internal_continuations": [wf[n]["budget"]["internal_continuations"] for n in names],
    "external_interventions": [wf[n]["budget"]["external_interventions"] for n in names],
}

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
x = np.arange(len(labels))
w = 0.25
colors = {"transitions_total": "#607d8b", "internal_continuations": "#4caf50",
          "external_interventions": "#f44336"}
for i, (metric, vals) in enumerate(metrics.items()):
    axes[0].bar(x + (i-1)*w, vals, w, label=metric.replace("_", " "), color=list(colors.values())[i])
axes[0].set_xticks(x); axes[0].set_xticklabels(labels)
axes[0].set_ylabel("count")
axes[0].legend(fontsize=8)
axes[0].set_title("Transition composition by contract architecture")

ratio = [wf[n]["budget"]["autonomy_ratio"] for n in names]
deepest = [wf[n]["budget"]["deepest_autonomous_run"] for n in names]
bars = axes[1].bar(labels, ratio, color=["#4caf50", "#2196f3"], width=0.45)
for bar, r_, d in zip(bars, ratio, deepest):
    axes[1].text(bar.get_x()+bar.get_width()/2, r_+0.03,
                 f"{r_:.2f}\n(deepest run: {d})", ha="center", fontsize=9)
axes[1].set_ylim(0, 1.1)
axes[1].set_ylabel("autonomy ratio (internal / total)")
axes[1].set_title("Autonomy ratio — same workflow, different architecture")

fig.suptitle("EXP-004 Autonomy Budget — static classification of the EXP-002 workflow", fontsize=12)
fig.tight_layout()
out = "/tmp/cfyow-work/results/EXP-004/viz/autonomy-budget.png"
Path(out).parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=150)
print("saved", out)
