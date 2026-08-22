from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "cfyow.exp003.dataset.case.v1"
BENCHMARK = "CFYOW Shared Consequence Benchmark"
MODULE = "EXP-003"


def _nested(obj: Any, *paths: str) -> Any:
    if not isinstance(obj, dict):
        return None
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


def _case_row(summary: dict[str, Any], experiment_id: str, case_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    github = summary.get("github") or {}
    metrics = payload.get("metrics") if isinstance(payload, dict) else None
    failure = payload.get("failure") if isinstance(payload, dict) else None

    row = {
        "schema_version": SCHEMA_VERSION,
        "benchmark": BENCHMARK,
        "module": MODULE,
        "experiment_id": experiment_id,
        "case_name": case_name,
        "run_id": github.get("run_id"),
        "run_attempt": github.get("run_attempt"),
        "github_sha": github.get("sha"),
        "network": summary.get("network"),
        "generated_at": summary.get("generated_at"),
        "status": payload.get("status"),
        "step_outcome": payload.get("step_outcome"),
        "parent_transaction_hash": payload.get("parent_transaction_hash"),
        "artifact_files": payload.get("artifact_files") or [],
        "failure_phase": _nested(failure, "phase"),
        "failure_error": _nested(failure, "error", "message"),
        "appeal_occurred": _nested(metrics, "appeal.occurred", "appeal_occurred"),
        "round_count": _nested(metrics, "round_count", "consensus.round_count", "after.parent.round_count"),
        "accepted_message_count": _nested(metrics, "accepted_message_count", "after.children.accepted_message_count"),
        "finalized_message_count": _nested(metrics, "finalized_message_count", "after.children.finalized_message_count"),
        "triggered_child_count": _nested(metrics, "triggered_child_count", "after.children.triggered_child_count"),
        "provisional_attempts": _nested(metrics, "after.provisional.attempts", "provisional_attempts"),
        "settled_attempts": _nested(metrics, "after.settled.attempts", "settled_attempts"),
        "provisional_duplicate_delta": _nested(metrics, "provisional_duplicate_delta"),
        "settled_duplicate_delta": _nested(metrics, "settled_duplicate_delta"),
        "stale_provisional": _nested(metrics, "stale_provisional"),
        "finality_latency_ms": _nested(metrics, "finality_latency_ms", "timing.accepted_to_finalized_ms"),
        "metrics": metrics,
    }
    return row


def rows_from_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _case_row(
            summary,
            "EXP-003A",
            "appeal-induced-duplicate-delivery",
            summary.get("exp003a_duplicate_delivery") or {},
        ),
        _case_row(
            summary,
            "EXP-003B",
            "semantic-overturn-under-changed-evidence",
            summary.get("exp003b_semantic_overturn") or {},
        ),
    ]


def _key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("run_id") or ""),
        str(row.get("run_attempt") or ""),
        str(row.get("experiment_id") or ""),
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def append_unique(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    existing = load_jsonl(path)
    seen = {_key(row) for row in existing}
    new_rows = [row for row in rows if _key(row) not in seen]
    if not new_rows:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in new_rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    return len(new_rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Append EXP-003 summary rows to the benchmark dataset")
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    added = append_unique(args.output, rows_from_summary(summary))
    print(f"EXP-003 dataset rows appended: {added}")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
