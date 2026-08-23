from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

BENCHMARK = "CFYOW Shared Consequence Benchmark"
SCHEMA = "cfyow.exp003.dataset.case.v1"

CASES = (
    ("EXP-003A", "appeal-induced-duplicate-delivery", "exp003a_duplicate_delivery"),
    ("EXP-003B", "semantic-overturn-under-changed-evidence", "exp003b_semantic_overturn"),
)


def nested(obj: dict[str, Any], *paths: str) -> Any:
    for path in paths:
        cur: Any = obj
        ok = True
        for part in path.split("."):
            if not isinstance(cur, dict) or part not in cur:
                ok = False
                break
            cur = cur[part]
        if ok:
            return cur
    return None


def metric(case: dict[str, Any], *names: str) -> Any:
    metrics = case.get("metrics") or {}
    payload = metrics.get("metrics") if isinstance(metrics, dict) else None
    if not isinstance(payload, dict):
        payload = metrics if isinstance(metrics, dict) else {}
    for name in names:
        if name in payload:
            return payload[name]
    return None


def make_row(summary: dict[str, Any], experiment_id: str, case_name: str, key: str) -> dict[str, Any]:
    case = summary.get(key) or {}
    failure = case.get("failure") or {}
    github = summary.get("github") or {}

    return {
        "schema_version": SCHEMA,
        "benchmark": BENCHMARK,
        "module": "EXP-003",
        "experiment_id": experiment_id,
        "case_name": case_name,
        "run_id": github.get("run_id"),
        "run_attempt": github.get("run_attempt"),
        "github_sha": github.get("sha"),
        "network": summary.get("network"),
        "generated_at": summary.get("generated_at"),
        "status": case.get("status"),
        "step_outcome": case.get("step_outcome"),
        "parent_transaction_hash": case.get("parent_transaction_hash"),
        "artifact_files": case.get("artifact_files") or [],
        "failure_phase": failure.get("phase") if isinstance(failure, dict) else None,
        "failure_error": failure.get("error") if isinstance(failure, dict) else None,
        "appeal_occurred": metric(case, "appeal_occurred"),
        "round_count": metric(case, "round_count", "consensus_round_count"),
        "accepted_message_count": metric(case, "accepted_message_count"),
        "finalized_message_count": metric(case, "finalized_message_count"),
        "triggered_child_count": metric(case, "triggered_child_count_after", "triggered_child_count"),
        "provisional_attempts": metric(case, "provisional_attempts_after"),
        "settled_attempts": metric(case, "settled_attempts_after"),
        "provisional_duplicate_delta": metric(case, "provisional_duplicate_delta"),
        "settled_duplicate_delta": metric(case, "settled_duplicate_delta"),
        "stale_provisional": metric(case, "stale_provisional_consequence_observed"),
        "finality_latency_ms": metric(case, "finality_latency_ms"),
        "metrics": case.get("metrics"),
    }


def load_existing(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row.get("run_id")), str(row.get("run_attempt")), str(row.get("experiment_id")))


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "benchmark", "module", "experiment_id", "case_name", "run_id", "run_attempt",
        "github_sha", "network", "generated_at", "status", "step_outcome",
        "parent_transaction_hash", "failure_phase", "failure_error", "appeal_occurred",
        "round_count", "accepted_message_count", "finalized_message_count",
        "triggered_child_count", "provisional_attempts", "settled_attempts",
        "provisional_duplicate_delta", "settled_duplicate_delta", "stale_provisional",
        "finality_latency_ms",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default="results/EXP-003/latest-bradbury.json")
    parser.add_argument("--output-dir", default="results/EXP-003/dataset")
    args = parser.parse_args()

    summary_path = Path(args.summary)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    existing_path = output_dir / "run-cases.jsonl"
    rows = load_existing(existing_path)
    by_key = {key(row): row for row in rows}

    for experiment_id, case_name, summary_key in CASES:
        row = make_row(summary, experiment_id, case_name, summary_key)
        by_key[key(row)] = row

    ordered = sorted(
        by_key.values(),
        key=lambda row: (str(row.get("generated_at") or ""), str(row.get("run_id") or ""), row["experiment_id"]),
    )

    existing_path.write_text(
        "".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in ordered),
        encoding="utf-8",
    )
    write_csv(ordered, output_dir / "run-cases.csv")

    valid = [row for row in ordered if row.get("status") == "VALID_RUN"]
    overview = {
        "schema_version": "cfyow.exp003.dataset.overview.v1",
        "benchmark": BENCHMARK,
        "rows": len(ordered),
        "valid_runs": len(valid),
        "invalid_or_no_result": len(ordered) - len(valid),
        "experiments": sorted({row["experiment_id"] for row in ordered}),
        "networks": sorted({row["network"] for row in ordered if row.get("network")}),
        "latest_generated_at": max((str(row.get("generated_at") or "") for row in ordered), default=None),
    }
    (output_dir / "overview.json").write_text(json.dumps(overview, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
