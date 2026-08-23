"""Generate EXP-002 comparison visualizations from the latest comparison dataset."""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTS = Path(__file__).resolve().parent.parent.parent / "results" / "EXP-002"
VIZ = RESULTS / "viz"


def latest_comparison() -> dict:
    files = sorted(glob.glob(str(RESULTS / "comparison-*.json")))
    if not files:
        raise SystemExit("no comparison datasets found")
    return json.loads(Path(files[-1]).read_text())


def main() -> None:
    data = latest_comparison()
    VIZ.mkdir(parents=True, exist_ok=True)
    runs = data["runs"]

    # ---- Chart 1: outcome divergence by arm -------------------------------
    arms = ["A_deterministic", "B_centralized_judge", "C_genlayer"]
    labels = ["A: Deterministic\n(ERC-8183-style)", "B: Centralized\nLLM judge", "C: GenLayer\nOptimistic Democracy"]
    outcome_sets = [data["summary"][a]["outcomes"] for a in arms]
    categories = sorted({k for s in outcome_sets for k in s})
    colors = {"completed": "#4caf50", "rejected": "#f44336",
              "PENDING_NETWORK": "#9e9e9e", "RUNNER_ERROR": "#ff9800",
              "failed_proposal": "#795548", "failed_accept": "#795548",
              "failed_evaluate": "#795548"}

    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = [0, 0, 0]
    for cat in categories:
        values = [s.get(cat, 0) for s in outcome_sets]
        ax.bar(labels, values, bottom=bottom, label=cat,
               color=colors.get(cat, "#607d8b"))
        bottom = [b + v for b, v in zip(bottom, values)]
    ax.set_title("EXP-002 — Identical workflows, three evaluator arms\n"
                 f"n={len(runs)} workflows · {data['generated_at'][:10]}")
    ax.set_ylabel("workflows")
    ax.legend(title="outcome")
    fig.tight_layout()
    fig.savefig(VIZ / "arm-outcomes.png", dpi=150)

    # ---- Chart 2: verdict vs evidence-reality -----------------------------
    # Ground truth: the evidence server genuinely serves a working /health,
    # but the submitted proof is only a digest. Verdicts reveal each arm's
    # epistemics, not service truth.
    fig, ax = plt.subplots(figsize=(10, 5))
    verdict_labels = ["A: predicate", "B: LLM judge", "C: consensus"]
    satisfied = [
        data["summary"]["A_deterministic"]["verdicts"].get("satisfied", 0),
        data["summary"]["B_centralized_judge"]["verdicts"].get("satisfied", 0),
        data["summary"]["C_genlayer"]["verdicts"].get("satisfied", 0),
    ]
    unsatisfied = [
        data["summary"]["A_deterministic"]["verdicts"].get("unsatisfied", 0),
        data["summary"]["B_centralized_judge"]["verdicts"].get("unsatisfied", 0),
        data["summary"]["C_genlayer"]["verdicts"].get("unsatisfied", 0),
    ]
    none_ct = [
        data["summary"]["A_deterministic"]["verdicts"].get("none", 0),
        data["summary"]["B_centralized_judge"]["verdicts"].get("none", 0),
        data["summary"]["C_genlayer"]["verdicts"].get("none", 0),
    ]
    x = range(len(verdict_labels))
    ax.bar([i - 0.22 for i in x], satisfied, width=0.22, label="satisfied", color="#4caf50")
    ax.bar(list(x), unsatisfied, width=0.22, label="unsatisfied", color="#f44336")
    ax.bar([i + 0.22 for i in x], none_ct, width=0.22, label="no verdict (pending)", color="#9e9e9e")
    ax.set_xticks(list(x))
    ax.set_xticklabels(["A\npredicate", "B\nLLM judge", "C\nconsensus"])
    ax.set_ylabel("workflows")
    ax.set_title("Verdict distribution — same evidence, different adjudication epistemics\n"
                 "Note: deterministic arm cannot detect unproven completion; judges can")
    ax.legend()
    fig.tight_layout()
    fig.savefig(VIZ / "verdict-distribution.png", dpi=150)

    # ---- Chart 3: cost & latency per arm -----------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    llm_calls = [
        data["summary"]["A_deterministic"]["total_llm_calls"],
        data["summary"]["B_centralized_judge"]["total_llm_calls"],
        data["summary"]["C_genlayer"]["total_llm_calls"],
    ]
    avg_wall = [
        data["summary"]["A_deterministic"]["avg_wall_ms"] or 0,
        data["summary"]["B_centralized_judge"]["avg_wall_ms"] or 0,
        0,  # C pending
    ]
    axes[0].bar(labels, llm_calls, color=["#4caf50", "#2196f3", "#9e9e9e"])
    axes[0].set_title("LLM calls per arm (judgment cost)")
    axes[0].set_ylabel("calls")
    axes[1].bar(labels, avg_wall, color=["#4caf50", "#2196f3", "#9e9e9e"])
    axes[1].set_title("Average wall time per workflow (ms)")
    axes[1].set_ylabel("ms")
    for ax in axes:
        ax.tick_params(axis="x", labelsize=8)
    fig.tight_layout()
    fig.savefig(VIZ / "cost-latency.png", dpi=150)

    print("charts written:")
    for p in sorted(VIZ.glob("*.png")):
        print(" ", p)


if __name__ == "__main__":
    main()
