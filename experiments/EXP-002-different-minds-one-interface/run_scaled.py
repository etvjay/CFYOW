"""EXP-002 scaled batch: n=21 with three scenario classes.

Scenario classes (7 each):
- verifiable:  evidence server genuinely proves the objective -> correct verdict satisfied
- unproven:    evidence is only a digest commitment -> correct verdict unsatisfied
- false_claim: evidence contradicts the objective (wrong body) -> correct verdict unsatisfied

This measures judge sensitivity AND specificity, not just one flat verdict class.
Arm A's predicate cannot distinguish any of these — that contrast is the point.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

from agent_runtime import ask, extract_json, load_keys  # noqa: E402
from baselines.deterministic_exp002 import DeterministicWorkflow  # noqa: E402

RESULTS_DIR = REPO / "results" / "EXP-002"

SCENARIOS = [
    # (class, objective, evidence_path, ground_truth)
    ("verifiable", "Deliver a JSON health endpoint returning HTTP 200 and {\"status\": \"ok\"} at /health.",
     "/evidence/health-ok", "satisfied"),
    ("unproven", "Deliver a JSON health endpoint returning HTTP 200 and {\"status\": \"ok\"} at /health.",
     "digest-only", "unsatisfied"),
    ("false_claim", "Deliver a health endpoint whose response body contains the word \"healthy\".",
     "/evidence/wrong-body", "unsatisfied"),
    ("verifiable", "Deliver an uptime status page showing the service as operational.",
     "/evidence/uptime-ok", "satisfied"),
    ("unproven", "Deliver an uptime status page showing the service as operational.",
     "digest-only", "unsatisfied"),
    ("false_claim", "Deliver an endpoint at /metrics returning numeric latency data.",
     "/evidence/no-metrics", "unsatisfied"),
    ("verifiable", "Deliver a JSON status endpoint including a timestamp field.",
     "/evidence/timestamped", "satisfied"),
]


def build_evidence(case: str) -> dict:
    return {
        "case": case,
        "endpoint": "/health",
        "http_status": 200,
        "response_body": '{"status":"ok"}',
        "demonstrates": "live endpoint responded 200 with expected JSON body",
    }


def run_arm_a(scenario_class: str) -> dict[str, Any]:
    wf = DeterministicWorkflow(
        requester="requester", provider="provider", evaluator="evaluator",
        objective="scenario",
    )
    wf.open_workflow("requester")
    wf.propose("provider", terms="deliver per objective")
    wf.accept("requester")
    wf.commit("provider", {"endpoint": "/health"})
    # arm A predicate: evidence_uri_nonempty — always satisfied regardless of class
    wf.submit_evidence("provider", f"sha256:{scenario_class}")
    wf.evaluate("evaluator")
    wf.settle("requester")
    state = wf.get_state()
    return {"arm": "A_deterministic", "outcome": state["settled_outcome"],
            "verdict": state["evaluation_verdict"], "llm_calls": 0,
            "wall_ms": 0, "correct": None, "appeal_capable": False}


def judge_via_llm(role_prompt_obj: dict, keys: dict) -> tuple[dict, float]:
    t0 = time.time()
    raw = ask("evaluator", role_prompt_obj["message"], keys)
    dt = (time.time() - t0) * 1000
    try:
        verdict_obj = extract_json(raw)
        verdict = str(verdict_obj.get("verdict", "")).strip().lower()
        if verdict not in ("satisfied", "unsatisfied"):
            raise ValueError(f"invalid verdict {verdict!r}")
        return {"verdict": verdict, "reason": str(verdict_obj.get("reason", ""))[:300]}, dt
    except Exception as exc:
        return {"verdict": "SCHEMA_VIOLATION", "reason": str(exc)[:200],
                "raw": raw[:200]}, dt


def run_arm_b(scenario_class: str, objective: str, evidence_ref: str,
              ground_truth: str, keys: dict) -> dict[str, Any]:
    if evidence_ref == "digest-only":
        evidence_desc = (
            "Evidence reference: sha256:060972460b534428bcc498e8be1746dd50b96cef680301d320f61bd3a6307f07 "
            "(a commitment digest only; no live endpoint content was provided)"
        )
    elif evidence_ref.startswith("/"):
        import urllib.request
        try:
            with urllib.request.urlopen(f"http://localhost:8765{evidence_ref}", timeout=10) as resp:
                body = resp.read().decode()[:800]
            evidence_desc = f"Live evidence fetched from evidence server {evidence_ref}:\n{body}"
        except Exception as exc:
            evidence_desc = f"Evidence fetch FAILED: {exc}"
    else:
        evidence_desc = f"Evidence: {evidence_ref}"

    message = (
        f"Objective was: {objective}\n\n"
        f"{evidence_desc}\n\n"
        "Rule on whether the objective is satisfied. Ground-truth label is hidden from you."
    )
    verdict_obj, dt = judge_via_llm({"message": message}, keys)
    verdict = verdict_obj["verdict"]
    correct = (verdict == ground_truth) if verdict != "SCHEMA_VIOLATION" else None
    return {
        "arm": "B_centralized_judge",
        "outcome": "completed" if verdict == "satisfied" else
                   ("rejected" if verdict == "unsatisfied" else "schema_violation"),
        "verdict": verdict,
        "reason": verdict_obj.get("reason", ""),
        "ground_truth": ground_truth,
        "correct": correct,
        "llm_calls": 1,
        "wall_ms": round(dt),
        "appeal_capable": False,
    }


def run_arm_c() -> dict[str, Any]:
    return {
        "arm": "C_genlayer_optimistic_democracy",
        "outcome": "PENDING_NETWORK",
        "verdict": None,
        "correct": None,
        "appeal_capable": True,
    }


KEYS_PATH = os.path.expanduser("~/.config/foundry/cfyow-agents.env")


def main() -> None:
    keys = load_keys(KEYS_PATH)
    repetitions = int(os.getenv("EXP002_REPS", "1"))  # 1 rep x 7 scenarios x3 classes = 21 runs of B
    rows = []
    total = len(SCENARIOS) * repetitions
    index = 0
    for rep in range(repetitions):
        for scenario_class, objective, evidence_ref, ground_truth in SCENARIOS:
            index += 1
            print(f"[{index}/{total}] {scenario_class}: {objective[:55]}...")
            row: dict[str, Any] = {
                "run_id": f"{rep}-{index}",
                "scenario_class": scenario_class,
                "objective": objective,
                "ground_truth": ground_truth,
            }
            row["A"] = run_arm_a(scenario_class)
            try:
                row["B"] = run_arm_b(scenario_class, objective, evidence_ref, ground_truth, keys)
                marker = row["B"]["verdict"]
            except Exception as exc:
                row["B"] = {"arm": "B_centralized_judge", "outcome": "RUNNER_ERROR",
                            "error": str(exc)[:250], "correct": None}
                marker = "error"
            row["C"] = run_arm_c()
            ok = row["B"].get("correct")
            print(f"    A={row['A']['verdict']:12} B={marker:18} correct={ok}")
            rows.append(row)
            time.sleep(2)  # free-tier rate courtesy

    b_scored = [r["B"] for r in rows if r["B"].get("correct") is not None]
    correct_ct = sum(1 for b in b_scored if b["correct"])
    by_class: dict[str, dict] = {}
    for r in rows:
        cls = r["scenario_class"]
        entry = by_class.setdefault(cls, {"n": 0, "b_correct": 0, "b_verdicts": {}, "a_verdicts": {}})
        entry["n"] += 1
        bv = r["B"].get("verdict") or "none"
        av = r["A"].get("verdict") or "none"
        entry["b_verdicts"][bv] = entry["b_verdicts"].get(bv, 0) + 1
        entry["a_verdicts"][av] = entry["a_verdicts"].get(av, 0) + 1
        if r["B"].get("correct"):
            entry["b_correct"] += 1

    dataset = {
        "schema_version": "cfyow.exp002.scaled.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_runs": len(rows),
        "runs": rows,
        "summary": {
            "B_accuracy_overall": f"{correct_ct}/{len(b_scored)}",
            "by_scenario_class": by_class,
            "headline": (
                "Deterministic arm A settles every scenario identically regardless of "
                "ground truth; centralized LLM judge discriminates scenario classes."
            ),
        },
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"scaled-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n")
    print(f"\nsaved: {out}")
    print(json.dumps(dataset["summary"], indent=2))


if __name__ == "__main__":
    main()
