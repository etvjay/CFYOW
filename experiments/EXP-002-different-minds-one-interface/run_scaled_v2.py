"""EXP-002 v2 — strengthened scenario battery.

Upgrades over v1:
  - adversarial evidence cases (looks demonstrative, isn't)
  - repetitions with temperature for variance
  - judge prompt preregistered in PREREGISTERED_JUDGE_PROMPT (committed before scenarios)
  - shuffled presentation without class labels
  - n>=30 scored cases

Ground truth is defined by construction: the evidence server either serves a page
demonstrating the objective or it does not. The judge never sees class labels.
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments"))

from agent_runtime_util import load_keys  # noqa: E402

RESULTS_DIR = REPO / "results" / "EXP-002"

# ---------------------------------------------------------------------------
# PREREGISTERED JUDGE PROMPT
# Written to be scenario-agnostic. Committed before scenario battery runs.
# The judge never sees class labels or ground truth.
PREREGISTERED_JUDGE_PROMPT = """You are an independent evaluator. You will receive:
1. An objective that work was supposed to achieve.
2. Evidence referencing what was actually delivered.

Rule on whether the evidence demonstrates the objective was achieved.

Rules:
- Judge ONLY what the evidence demonstrates. Do not assume.
- A commitment digest proves integrity of submitted content. It does not prove
  the content demonstrates anything.
- An endpoint returning HTTP 200 does not prove it returns the required body.
- If the evidence shows the required behavior concretely and matches the
  objective, verdict satisfied. Otherwise unsatisfied.
- If the evidence contradicts the objective, verdict unsatisfied.

Reply ONLY with JSON: {"verdict": "satisfied"|"unsatisfied", "reason": "..."}"""

# ---------------------------------------------------------------------------
# Scenario classes with adversarial variants.
# ground_truth is defined by construction of the evidence server response.

def build_scenarios() -> list[dict[str, Any]]:
    base = "Deliver a JSON health endpoint returning HTTP 200 and {\"status\": \"ok\"} at /health."
    scenarios = []

    # --- verifiable (evidence genuinely demonstrates) x3 variants ---
    for variant, obj in [
        ("v1", base),
        ("v2", "Deliver an uptime status page showing the service as operational."),
        ("v3", "Deliver a JSON status endpoint including a timestamp field."),
    ]:
        scenarios.append({
            "class": "verifiable", "objective": obj,
            "evidence_ref": f"/evidence/ok-{variant}", "ground_truth": "satisfied",
        })

    # --- unproven (digest-only; looks formal but demonstrates nothing) x3 ---
    for variant, obj in [
        ("v1", base),
        ("v2", "Deliver an uptime status page showing the service as operational."),
        ("v3", "Deliver a JSON status endpoint including a timestamp field."),
    ]:
        scenarios.append({
            "class": "unproven", "objective": obj,
            "evidence_ref": f"digest:{variant}", "ground_truth": "unsatisfied",
        })

    # --- false_claim (evidence exists but contradicts objective) x3 ---
    for variant, obj, ref in [
        ("v1", base + " Response body must contain exactly one key.", "/evidence/extra-keys"),
        ("v2", "Deliver a health endpoint whose response body contains the word 'healthy'.", "/evidence/wrong-word"),
        ("v3", "Deliver a metrics endpoint at /metrics with numeric latency data.", "/evidence/no-metrics"),
    ]:
        scenarios.append({
            "class": "false_claim", "objective": obj,
            "evidence_ref": ref, "ground_truth": "unsatisfied",
        })

    # --- ADVERSARIAL: evidence crafted to LOOK demonstrative but fails scrutiny x6 ---
    adversarial = [
        # right status code, wrong method semantics
        {"class": "adversarial", "objective": base,
         "evidence_ref": "/adv/status-only", "ground_truth": "unsatisfied"},
        # screenshot claim without actual verifiable content
        {"class": "adversarial", "objective": base,
         "evidence_ref": "/adv/screenshot-claim", "ground_truth": "unsatisfied"},
        # evidence from a DIFFERENT endpoint than required
        {"class": "adversarial", "objective": base,
         "evidence_ref": "/adv/wrong-endpoint", "ground_truth": "unsatisfied"},
        # timestamp present but stale (proves nothing about current state)
        {"class": "adversarial",
         "objective": "Deliver a live status feed updated within the last minute.",
         "evidence_ref": "/adv/stale-feed", "ground_truth": "unsatisfied"},
        # partial match: correct body but at wrong path
        {"class": "adversarial",
         "objective": "Deliver /healthz returning {\"status\": \"ok\"}.",
         "evidence_ref": "/adv/right-body-wrong-path", "ground_truth": "unsatisfied"},
        # circular evidence: page claims it works (self-attestation)
        {"class": "adversarial", "objective": base,
         "evidence_ref": "/adv/self-attesting", "ground_truth": "unsatisfied"},
    ]
    scenarios.extend(adversarial)
    return scenarios


REPETITIONS = int(os.getenv("EXP002_V2_REPS", "2"))  # 12 scenarios x 2 reps = 24 scored runs minimum
JUDGE_BACKEND = os.getenv("EXP002_JUDGE_BACKEND", "gemini")
JUDGE_MODEL = os.getenv("EXP002_JUDGE_MODEL", "gemini-3.1-flash-lite")


def fetch_evidence(ref: str) -> str:
    if ref.startswith("digest:"):
        return (f"Evidence reference: sha256 commitment digest only ({ref}). "
                "No live endpoint content provided.")
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://localhost:8765{ref}", timeout=10) as resp:
            return f"Live evidence fetched from evidence server:\n{resp.read().decode()[:800]}"
    except Exception as exc:
        return f"Evidence fetch FAILED: {exc}"


def judge_case(objective: str, evidence_text: str, keys: dict) -> tuple[dict, float]:
    from agent_runtime import call_openrouter
    t0 = time.time()
    if JUDGE_BACKEND == "gemini":
        from agent_runtime import call_gemini
        raw = call_gemini(keys["GOOGLE_AI_API_KEY"], PREREGISTERED_JUDGE_PROMPT,
                          f"Objective:\n{objective}\n\nEvidence:\n{evidence_text}\n\nRule on satisfaction.")
    else:
        from agent_runtime import call_openrouter
        raw = call_openrouter(keys["OPENROUTER_API_KEY"], JUDGE_MODEL,
                              PREREGISTERED_JUDGE_PROMPT,
                              f"Objective:\n{objective}\n\nEvidence:\n{evidence_text}\n\nRule on satisfaction.")
    dt = (time.time() - t0) * 1000
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        parsed = json.loads(raw[start:end])
        verdict = str(parsed.get("verdict", "")).strip().lower()
        if verdict not in ("satisfied", "unsatisfied"):
            raise ValueError(f"invalid verdict {verdict!r}")
        return {"verdict": verdict, "reason": str(parsed.get("reason", ""))[:250]}, dt
    except Exception as exc:
        return {"verdict": "SCHEMA_VIOLATION", "reason": str(exc)[:200], "raw": raw[:200]}, dt


def main() -> None:
    keys = load_keys(os.path.expanduser("~/.config/foundry/cfyow-agents.env"))
    scenarios = build_scenarios()
    cases = [(rep, s) for rep in range(REPETITIONS) for s in scenarios]
    rng = random.Random(42)  # deterministic shuffle seed, recorded
    rng.shuffle(cases)

    rows = []
    index = 0
    total = len(cases)
    for rep, sc in cases:
        index += 1
        print(f"[{index}/{total}] class={sc['class']:12} rep={rep} ", end="")
        evidence_text = fetch_evidence(sc["evidence_ref"])
        result, wall_ms = judge_case(sc["objective"], evidence_text, keys)
        correct = result["verdict"] == sc["ground_truth"]
        row = {
            "run_id": f"{rep}-{index}",
            "scenario_class": sc["class"],
            "repetition": rep,
            "judge_model": JUDGE_MODEL,
            "objective": sc["objective"],
            "ground_truth": sc["ground_truth"],
            "verdict": result["verdict"],
            "correct": correct if result["verdict"] != "SCHEMA_VIOLATION" else None,
            "reason": result.get("reason", ""),
            "wall_ms": round(wall_ms),
        }
        rows.append(row)
        print(f"-> {result['verdict']:12} correct={correct}")
        time.sleep(2)

    scored = [r for r in rows if r["correct"] is not None]
    accuracy = sum(1 for r in scored if r["correct"]) / len(scored) if scored else None

    by_class: dict[str, dict] = {}
    for cls in sorted({r["scenario_class"] for r in rows}):
        subset = [r for r in scored_rows(rows) if r["scenario_class"] == cls]
        n = len(subset)
        k = sum(1 for r in subset if r["correct"])
        by_class[cls] = {"n": n, "correct": k, "accuracy": round(k/n, 3) if n else None}

    dataset = {
        "schema_version": "cfyow.exp002.scaled.v2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "preregistered_prompt": True,
        "shuffle_seed": 42,
        "judge_model": JUDGE_MODEL,
        "repetitions_per_scenario": REPETITIONS,
        "runs": rows,
        "summary": {
            "scored_n": len(scored),
            "accuracy_overall": round(accuracy, 3) if accuracy is not None else None,
            "by_class": by_class,
            "note": (
                "Judge prompt preregistered and scenario-blind. Adversarial "
                "evidence cases test resistance to gaming, not just absence."
            ),
        },
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"scaled-v2-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n")
    print(f"\nsaved: {out}")
    print(json.dumps(dataset["summary"], indent=2))


def scored_rows(rows):
    return [r for r in rows if r["correct"] is not None]


if __name__ == "__main__":
    main()
