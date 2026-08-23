"""Evidence lineage for CFYOW (M1 completion).

Chains every captured run into the control-plane lineage graph:

    Hypothesis -> Scenario -> Contract(+source SHA) -> Tx hashes -> Dataset

LineageNode = one link in that chain; LineageGraph = the full chain for one
experiment, content-addressed so any tampering with an upstream artifact
breaks downstream hashes. Append-only: nodes are never mutated.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def git_file_sha(repo_root: str | Path, rel_path: str) -> str | None:
    """Blob SHA of a file as committed — None if not tracked."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", f"HEAD:{rel_path}"],
            cwd=str(repo_root), stderr=subprocess.DEVNULL, text=True,
        )
        return out.strip()
    except Exception:
        return None


@dataclass
class LineageNode:
    kind: str            # hypothesis | scenario | contract | transactions | dataset
    label: str
    payload: dict[str, Any]
    parents: list[str] = field(default_factory=list)  # node ids
    node_id: str = ""

    def __post_init__(self) -> None:
        if not self.node_id:
            self.node_id = self.compute_id()

    def compute_id(self) -> str:
        return hashlib.sha256(
            canonical({"kind": self.kind, "label": self.label,
                       "payload": self.payload,
                       "parents": sorted(self.parents)}).encode()
        ).hexdigest()[:16]


class LineageGraph:
    """Append-only lineage chain for one experiment."""

    SCHEMA = "cfyow.lineage.v1"

    def __init__(self, experiment_id: str, hypothesis: str, falsifier: str):
        self.experiment_id = experiment_id
        self.nodes: dict[str, LineageNode] = {}
        self.root = LineageNode(
            kind="hypothesis",
            label=f"{experiment_id}:hypothesis",
            payload={"statement": hypothesis, "falsifier": falsifier},
        )
        self.add(self.root)

    def add(self, node: LineageNode) -> LineageNode:
        if node.node_id in self.nodes:
            return self.nodes[node.node_id]  # idempotent append
        # parent must exist — no orphan links
        missing = [p for p in node.parents if p not in self.nodes]
        if missing:
            raise ValueError(f"unknown parent node(s): {missing}")
        self.nodes[node.node_id] = node
        return node

    def add_scenario(self, scenario_id: str, scenario_input: dict) -> LineageNode:
        return self.add(LineageNode(
            kind="scenario", label=scenario_id,
            payload={"input": scenario_input, "input_hash": content_hash(scenario_input)},
            parents=[self.root.node_id],
        ))

    def add_contract(self, scenario_node: LineageNode, contract_path: str,
                     repo_root: str | Path = ".") -> LineageNode:
        sha = git_file_sha(repo_root, contract_path)
        source = Path(repo_root) / contract_path
        code_hash = content_hash(source.read_text()) if source.exists() else None
        return self.add(LineageNode(
            kind="contract", label=contract_path,
            payload={"git_blob_sha": sha or "uncommitted", "content_sha256": code_hash},
            parents=[scenario_node.node_id],
        ))

    def add_transactions(self, parent: LineageNode, tx_hashes: list[str]) -> LineageNode:
        return self.add(LineageNode(
            kind="transactions",
            label=f"txs:{parent.label}",
            payload={"hashes": sorted(tx_hashes), "count": len(tx_hashes)},
            parents=[parent.node_id],
        ))

    def add_dataset(self, parent: LineageNode, dataset_path: str | Path) -> LineageNode:
        path = Path(dataset_path)
        payload: dict[str, Any] = {"path": str(path)}
        if path.exists():
            payload["file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        return self.add(LineageNode(
            kind="dataset", label=path.name, payload=payload,
            parents=[parent.node_id],
        ))

    def verify(self) -> tuple[bool, list[str]]:
        """Recompute every node id; any mismatch = tampering or broken link."""
        problems = []
        for node in self.nodes.values():
            if node.node_id != node.compute_id():
                problems.append(f"hash mismatch at {node.label}")
            for p in node.parents:
                if p not in self.nodes:
                    problems.append(f"dangling parent {p} on {node.label}")
        return (not problems), problems

    def to_dict(self) -> dict[str, Any]:
        ok, problems = self.verify()
        return {
            "schema_version": self.SCHEMA,
            "experiment_id": self.experiment_id,
            "verified": ok,
            "verification_problems": problems,
            "nodes": [
                {"node_id": n.node_id, "kind": n.kind, "label": n.label,
                 "parents": n.parents, "payload": n.payload}
                for n in self.nodes.values()
            ],
        }

    def save(self, destination: str | Path) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n")
        os.replace(tmp, path)
        return path


import os  # noqa: E402  (used by save's atomic replace)
