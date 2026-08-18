"""CLI for the Experiment Ledger.

Examples:
    python -m experiment_ledger run experiments/EXP-001-judgment-boundary/baseline-manifest.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import write_run
from .manifest import build_run_from_manifest

DEFAULT_REGISTRY = Path("experiment_ledger/registry/baselines.json")


def main() -> int:
    parser = argparse.ArgumentParser(prog="experiment-ledger")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="execute a manifest and capture JSON")
    run_parser.add_argument("manifest")
    run_parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    run_parser.add_argument("--output", default=None)
    run_parser.add_argument("--run-id", default=None)

    validate_parser = sub.add_parser("validate", help="perform structural validation")
    validate_parser.add_argument("run_json")

    args = parser.parse_args()

    if args.command == "run":
        assembled = build_run_from_manifest(args.manifest, args.registry)
        payload = assembled.execute(run_id=args.run_id)
        output = args.output or f"results/{payload['experiment_id']}/runs/{payload['run_id']}.json"
        path = write_run(payload, output)
        print(path)
        return 0 if payload["status"] != "INVALID_RUN" else 2

    payload = json.loads(Path(args.run_json).read_text(encoding="utf-8"))
    errors = validate_run_structure(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("valid")
    return 0


def validate_run_structure(payload: dict) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version",
        "experiment_id",
        "run_id",
        "hypothesis",
        "provenance",
        "scenario",
        "implementations",
        "evidence",
        "interpretation",
    }
    missing = required - payload.keys()
    if missing:
        errors.append(f"missing top-level fields: {sorted(missing)}")
    if payload.get("schema_version") != "experiment-ledger.v1":
        errors.append("unsupported schema_version")
    implementations = payload.get("implementations", [])
    if not implementations:
        errors.append("no implementations captured")
    ids = [item.get("id") for item in implementations]
    if len(ids) != len(set(ids)):
        errors.append("duplicate implementation ids")
    if payload.get("evidence", {}).get("missing_declared_baselines"):
        errors.append("declared baselines are missing from capture")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
