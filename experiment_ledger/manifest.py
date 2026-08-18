"""Manifest-driven experiment assembly."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from .core import ExperimentRun, ImplementationSpec, sha256_file


def _load_entrypoint(spec: str):
    module_name, function_name = spec.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


def load_registry(path: str | Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {item["baseline_id"]: item for item in payload["baselines"]}


def build_run_from_manifest(
    manifest_path: str | Path,
    registry_path: str | Path,
    repo_root: str | Path = ".",
) -> ExperimentRun:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    registry = load_registry(registry_path)
    implementations: list[ImplementationSpec] = []

    for baseline_id in manifest.get("baselines", []):
        if baseline_id not in registry:
            raise KeyError(f"undeclared baseline: {baseline_id}")
        baseline = registry[baseline_id]
        implementation_path = Path(repo_root) / baseline["implementation"]
        version = (
            f"sha256:{sha256_file(implementation_path)}"
            if implementation_path.exists()
            else "missing-source"
        )
        implementations.append(
            ImplementationSpec(
                id=baseline_id,
                klass="baseline",
                runner=_load_entrypoint(baseline["entrypoint"]),
                version=version,
                metadata={
                    "type": baseline["type"],
                    "implementation": baseline["implementation"],
                    "trust_model": baseline["trust_model"],
                },
            )
        )

    for target in manifest.get("targets", []):
        implementations.append(
            ImplementationSpec(
                id=target["id"],
                klass="target",
                runner=_load_entrypoint(target["entrypoint"]),
                version=target.get("version", "unspecified"),
                metadata=target.get("metadata", {}),
            )
        )

    return ExperimentRun(
        experiment_id=manifest["experiment_id"],
        hypothesis=manifest["hypothesis"]["statement"],
        falsifier=manifest["hypothesis"]["falsifier"],
        scenario_id=manifest["scenario"]["id"],
        scenario_input=manifest["scenario"]["input"],
        implementations=implementations,
        repo_root=repo_root,
    )
