"""Experiment Ledger v1 core capture primitives.

This module records experiment declarations and observations. It deliberately
keeps evidence capture separate from interpretation.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

RUNNER_VERSION = "0.1.0"
VALID_IMPL_STATUSES = {"SUCCESS", "FAILURE", "PARTIAL", "INVALID_RUN"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_value(args: list[str], cwd: str | Path = ".") -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=cwd, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return "unknown"


def environment_fingerprint(repo_root: str | Path = ".") -> dict[str, Any]:
    root = Path(repo_root)
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "executable": sys.executable,
        "repository": git_value(["config", "--get", "remote.origin.url"], root),
        "commit_sha": git_value(["rev-parse", "HEAD"], root),
        "branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"], root),
    }


@dataclass(frozen=True)
class ImplementationSpec:
    id: str
    klass: str
    runner: Callable[[dict[str, Any]], Any]
    version: str = "unspecified"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.klass not in {"baseline", "target"}:
            raise ValueError("klass must be baseline or target")


class ExperimentRun:
    def __init__(
        self,
        experiment_id: str,
        hypothesis: str,
        falsifier: str,
        scenario_id: str,
        scenario_input: dict[str, Any],
        implementations: list[ImplementationSpec],
        repo_root: str | Path = ".",
    ) -> None:
        if not implementations:
            raise ValueError("at least one implementation must be declared")
        ids = [item.id for item in implementations]
        if len(ids) != len(set(ids)):
            raise ValueError("implementation ids must be unique")

        self.experiment_id = experiment_id
        self.hypothesis = hypothesis
        self.falsifier = falsifier
        self.scenario_id = scenario_id
        self.scenario_input = scenario_input
        self.implementations = implementations
        self.repo_root = Path(repo_root)

    def execute(self, run_id: str | None = None) -> dict[str, Any]:
        run_id = run_id or f"{self.experiment_id}-{time.time_ns()}"
        env = environment_fingerprint(self.repo_root)
        results: list[dict[str, Any]] = []

        for spec in self.implementations:
            started = time.perf_counter_ns()
            errors: list[dict[str, Any]] = []
            result: Any = None
            status = "SUCCESS"
            try:
                result = spec.runner(self.scenario_input)
            except Exception as exc:  # Evidence capture must preserve failures.
                status = "FAILURE"
                errors.append({
                    "type": type(exc).__name__,
                    "message": str(exc),
                })
            elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
            results.append({
                "id": spec.id,
                "class": spec.klass,
                "status": status,
                "version": spec.version,
                "metadata": spec.metadata,
                "result": result,
                "metrics": {"wall_time_ms": elapsed_ms},
                "errors": errors,
                "artifacts": [],
            })

        baseline_ids = {s.id for s in self.implementations if s.klass == "baseline"}
        observed_ids = {r["id"] for r in results}
        missing = sorted(baseline_ids - observed_ids)
        run_status = "INVALID_RUN" if missing else self._aggregate_status(results)

        return {
            "schema_version": "experiment-ledger.v1",
            "experiment_id": self.experiment_id,
            "run_id": run_id,
            "status": run_status,
            "hypothesis": {
                "statement": self.hypothesis,
                "falsifier": self.falsifier,
            },
            "provenance": {
                "repository": env["repository"],
                "commit_sha": env["commit_sha"],
                "branch": env["branch"],
                "runner_version": RUNNER_VERSION,
                "environment": env,
            },
            "scenario": {
                "id": self.scenario_id,
                "input_hash": sha256_value(self.scenario_input),
                "input": self.scenario_input,
            },
            "implementations": results,
            "comparison": self._comparison(results),
            "evidence": {
                "raw_artifacts": [],
                "logs": [],
                "transaction_hashes": [],
                "receipts": [],
                "missing_declared_baselines": missing,
            },
            "interpretation": {
                "status": "UNREVIEWED",
                "observations": [],
                "claims_supported": [],
                "claims_weakened": [],
            },
        }

    @staticmethod
    def _aggregate_status(results: list[dict[str, Any]]) -> str:
        statuses = {r["status"] for r in results}
        if statuses == {"SUCCESS"}:
            return "SUCCESS"
        if "INVALID_RUN" in statuses:
            return "INVALID_RUN"
        if statuses == {"FAILURE"}:
            return "FAILURE"
        return "PARTIAL"

    @staticmethod
    def _comparison(results: list[dict[str, Any]]) -> dict[str, Any]:
        successful = [r for r in results if r["status"] == "SUCCESS"]
        return {
            "successful_implementations": [r["id"] for r in successful],
            "failed_implementations": [
                r["id"] for r in results if r["status"] != "SUCCESS"
            ],
            "result_hashes": {
                r["id"]: sha256_value(r["result"]) for r in successful
            },
            "wall_time_ms": {
                r["id"]: r["metrics"]["wall_time_ms"] for r in results
            },
        }


def write_run(run: dict[str, Any], destination: str | Path) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(run, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, path)
    return path
