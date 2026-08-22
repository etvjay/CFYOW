import json
from pathlib import Path

import pytest

from experiment_ledger.__main__ import validate_run_structure
from experiment_ledger.core import ExperimentRun, ImplementationSpec, write_run
from experiment_ledger.manifest import build_run_from_manifest


def test_capture_preserves_success_and_failure(tmp_path):
    def ok(_scenario):
        return {"decision": True}

    def boom(_scenario):
        raise RuntimeError("expected failure")

    run = ExperimentRun(
        experiment_id="EXP-T",
        hypothesis="target differs",
        falsifier="target does not differ",
        scenario_id="s1",
        scenario_input={"x": 1},
        implementations=[
            ImplementationSpec("baseline-ok", "baseline", ok, "v1"),
            ImplementationSpec("target-fail", "target", boom, "v1"),
        ],
        repo_root=tmp_path,
    ).execute("run-1")

    assert run["status"] == "PARTIAL"
    assert run["implementations"][0]["status"] == "SUCCESS"
    assert run["implementations"][1]["status"] == "FAILURE"
    assert run["implementations"][1]["errors"][0]["type"] == "RuntimeError"
    assert run["interpretation"]["status"] == "UNREVIEWED"


def test_write_run_is_valid_json(tmp_path):
    payload = {
        "schema_version": "experiment-ledger.v1",
        "experiment_id": "E",
        "run_id": "R",
        "hypothesis": {},
        "provenance": {},
        "scenario": {},
        "implementations": [{"id": "x"}],
        "evidence": {"missing_declared_baselines": []},
        "interpretation": {},
    }
    destination = write_run(payload, tmp_path / "run.json")
    assert json.loads(destination.read_text()) == payload
    assert not (tmp_path / "run.json.tmp").exists()


def test_validator_rejects_missing_baselines():
    payload = {
        "schema_version": "experiment-ledger.v1",
        "experiment_id": "E",
        "run_id": "R",
        "hypothesis": {},
        "provenance": {},
        "scenario": {},
        "implementations": [{"id": "x"}],
        "evidence": {"missing_declared_baselines": ["baseline-y"]},
        "interpretation": {},
    }
    errors = validate_run_structure(payload)
    assert "declared baselines are missing from capture" in errors


def test_exp001_manifest_discovers_every_registered_baseline():
    assembled = build_run_from_manifest(
        "experiments/EXP-001-judgment-boundary/baseline-manifest.json",
        "experiment_ledger/registry/baselines.json",
    )
    assert [spec.id for spec in assembled.implementations] == [
        "deterministic-attestation-v1",
        "centralized-adjudicator-v1",
    ]


def test_manifest_rejects_unknown_baseline(tmp_path):
    manifest = {
        "experiment_id": "E",
        "hypothesis": {"statement": "s", "falsifier": "f"},
        "scenario": {"id": "s", "input": {}},
        "baselines": ["does-not-exist"],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps({"baselines": []}))

    with pytest.raises(KeyError, match="undeclared baseline"):
        build_run_from_manifest(manifest_path, registry_path, repo_root=tmp_path)
