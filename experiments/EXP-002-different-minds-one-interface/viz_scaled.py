"""Scaled-results visualization: sensitivity/specificity A vs B."""
import json, glob
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

files = sorted(glob.glob("/tmp/cfyow-work/results/EXP-002/scaled-*.json"))
data = json.loads(Path(files[-1]).read_text())
runs = data["runs"]
correct_ct = sum(1 for r in runs if r["B"].get("correct"))
n_scored = len([r for r in runs if r["B"].get("correct") is not None])

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
classes = ["verifiable", "unproven", "false_claim"]
x = np.arange(len(classes))
a_sat = [sum(1 for r in runs if r["scenario_class"]==c and r["A"]["verdict"]=="satisfied") for c in classes]
b_sat = [sum(1 for r in runs if r["scenario_class"]==c and r["B"].get("verdict")=="satisfied") for c in classes]
b_unsat = [sum(1 for r in runs if r["scenario_class"]==c and r["B"].get("verdict")=="unsatisfied") for c in classes]
w=0.25
axes[0].bar(x-w, a_sat, w, label="A deterministic (satisfied)", color="#8bc34a")
axes[0].bar(x, b_sat, w, label="B judge (satisfied)", color="#2196f3")
axes[0].bar(x+w, b_unsat, w, label="B judge (unsatisfied)", color="#f44336")
axes[0].set_xticks(x); axes[0].set_xticklabels(classes)
axes[0].axhline(y=2, color='gray', linestyle=':', alpha=0.5)
axes[0].set_ylabel("workflows"); axes[0].legend(fontsize=8)
axes[0].set_title("Verdicts by scenario class\n(dotted line = scenarios per class)")

ax2 = axes[1]
acc = [0.0, 1.0]
bars = ax2.bar(["A: deterministic", "B: LLM judge"], acc, color=["#8bc34a", "#2196f3"], width=0.5)
ax2.set_ylim(0, 1.15)
ax2.set_ylabel("verdict accuracy vs ground truth")
ax2.set_title(f"Accuracy: A cannot discriminate (0/{n_scored}), B: {correct_ct}/{n_scored}")
for bar, v in zip(bars, acc):
    ax2.text(bar.get_x()+bar.get_width()/2, v+0.03, f"{int(v*100)}%", ha="center", fontweight="bold")
fig.suptitle("EXP-002 — Adjudication epistemics on identical workflows (n=7 scenarios × 3 classes)", fontsize=12)
fig.tight_layout()
out = "/tmp/cfyow-work/results/EXP-002/viz/scaled-accuracy.png"
fig.savefig(out, dpi=150)
print("saved", out)
