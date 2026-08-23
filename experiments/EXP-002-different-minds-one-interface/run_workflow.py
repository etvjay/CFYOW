"""EXP-002 workflow runner: drives one full propose→settle cycle with real agents.

Agents interact only via protocol-visible messages. The runner is transport,
not orchestrator: it carries messages between agents and the interface, but
makes no decisions. All events logged for instrumentation.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_runtime import AGENTS, ask, extract_json, load_keys  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "results" / "EXP-002"


def run_workflow(objective: str, keys_path: str) -> dict[str, Any]:
    keys = load_keys(keys_path)
    log: list[dict[str, Any]] = []
    schema_fields_used: set[str] = set()

    def event(kind: str, actor: str, payload: Any, latency_ms: float | None = None):
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            "actor": actor,
            "payload": payload,
        }
        if latency_ms is not None:
            entry["latency_ms"] = round(latency_ms)
        log.append(entry)
        print(f"  [{kind}] {actor}: {json.dumps(payload)[:120]}")

    # ---- 1. requester defines objective (given by harness as scenario input)

    # ---- 2. provider proposes terms
    t0 = time.time()
    raw = ask("provider", f"Objective from the shared interface:\n{objective}\n\nPropose your terms.", keys)
    dt = (time.time() - t0) * 1000
    try:
        proposal = extract_json(raw)
        terms = str(proposal.get("terms", "")).strip()
        event("llm_raw_violation" if not terms else "propose", "provider",
              {"terms": terms} if terms else {"raw": raw[:300]}, dt)
        if not terms:
            raise ValueError("empty terms")
    except Exception as exc:  # schema violation is data, not crash
        event("schema_violation", "provider", {"error": str(exc), "raw": raw[:300]}, dt)
        return _finish(log, "failed_proposal", schema_fields_used)

    # ---- 3. requester accepts or rejects
    t0 = time.time()
    raw = ask("requester", f"Proposal on the shared interface:\n{terms}\n\nAccept?", keys)
    dt = (time.time() - t0) * 1000
    try:
        decision = extract_json(raw)
        accept = bool(decision.get("accept"))
        schema_fields_used.update({"accept", "reason"} & set(decision.keys()))
        event("accept" if accept else "reject", "requester", decision, dt)
        if not accept:
            return _finish(log, "rejected_at_accept", schema_fields_used)
    except Exception as exc:
        event("schema_violation", "requester", {"error": str(exc), "raw": raw[:300]}, dt)
        return _finish(log, "failed_accept", schema_fields_used)

    # ---- 4. provider commits + submits evidence (deliverable digest commitment)
    deliverable = {
        "endpoint": "/health",
        "response": '{"status":"ok"}',
        "timeline": "delivered within proposal window",
    }
    import hashlib

    digest = hashlib.sha256(json.dumps(deliverable, sort_keys=True).encode()).hexdigest()
    evidence_uri = f"sha256:{digest}"
    event("commit", "provider", {"digest": digest})
    event("submit_evidence", "provider", {"evidence_uri": evidence_uri})

    # ---- 5. evaluator judges (adversarial)
    t0 = time.time()
    raw = ask(
        "evaluator",
        "Evidence submitted on the shared interface.\n"
        f"Objective was: {objective}\n"
        f"Evidence reference: {evidence_uri}\n"
        f"Committed digest matches submission: yes\n\n"
        "Rule on whether the objective is satisfied.",
        keys,
    )
    dt = (time.time() - t0) * 1000
    try:
        verdict_obj = extract_json(raw)
        verdict = str(verdict_obj.get("verdict", "")).strip().lower()
        schema_fields_used.update({"verdict", "reason"} & set(verdict_obj.keys()))
        event("evaluate", "evaluator", verdict_obj, dt)
        if verdict not in ("satisfied", "unsatisfied"):
            raise ValueError(f"invalid verdict {verdict!r}")
    except Exception as exc:
        event("schema_violation", "evaluator", {"error": str(exc), "raw": raw[:300]}, dt)
        return _finish(log, "failed_evaluate", schema_fields_used)

    outcome = "completed" if verdict == "satisfied" else "rejected"
    event("settle", "interface", {"outcome": outcome})
    return _finish(log, outcome, schema_fields_used)


def _finish(log: list, outcome: str, fields: set[str]) -> dict[str, Any]:
    latencies = [e["latency_ms"] for e in log if "latency_ms" in e]
    result = {
        "schema_version": "cfyow.exp002.workflow.v1",
        "outcome": outcome,
        "interpretation": {"status": "UNREVIEWED"},
        "metrics": {
            "event_count": len(log),
            "llm_calls": sum(1 for e in log if e["kind"] in ("propose", "accept", "reject", "evaluate")),
            "schema_violations": sum(1 for e in log if e["kind"] == "schema_violation"),
            "avg_llm_latency_ms": round(sum(latencies) / len(latencies)) if latencies else None,
            "max_llm_latency_ms": round(max(latencies)) if latencies else None,
            "schema_fields_observed": sorted(fields),
        },
        "log": log,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RESULTS_DIR / f"workflow-{stamp}.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"\nsaved: {path}")
    return result


if __name__ == "__main__":
    keys_file = os.getenv(
        "EXP002_KEYS", os.path.expanduser("~/.config/foundry/cfyow-agents.env")
    )
    obj = (
        os.getenv("EXP002_OBJECTIVE")
        or "Deliver a working JSON health endpoint that returns HTTP 200 and "
        '{\\"status\\": \\"ok\\"} at /health.'
    )
    print(f"=== EXP-002 workflow run ===\nobjective: {obj}\n")
    result = run_workflow(obj, keys_file)
    print(f"\noutcome: {result['outcome']}")
    print(json.dumps(result["metrics"], indent=2))
