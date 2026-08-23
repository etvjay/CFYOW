"""Tests for evidence lineage (M1)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from experiment_ledger.lineage import (
    LineageGraph, LineageNode, content_hash,
)


def test_chain_hypothesis_scenario_contract_dataset():
    g = LineageGraph("EXP-002", "coordination via adjudicated interface", "hidden context required")
    scenario = g.add_scenario("sc-1", {"objective": "deliver /health"})
    contract = g.add_contract(scenario, "contracts/different_minds_judged.py")
    txs = g.add_transactions(contract, ["0xabc", "0xdef"])
    ds_path = Path(__file__).resolve().parent.parent.parent / "results" / "EXP-002" / "lineage-test-dataset.json"
    ds_path.parent.mkdir(parents=True, exist_ok=True)
    ds_path.write_text('{"result": 1}')
    dataset = g.add_dataset(txs, ds_path)
    ds_path.unlink()

    ok, problems = g.verify()
    assert ok, problems
    d = g.to_dict()
    assert d["verified"] is True
    kinds = [n["kind"] for n in d["nodes"]]
    for expected in ("hypothesis", "scenario", "contract", "transactions", "dataset"):
        assert expected in kinds


def test_append_only_no_orphans():
    g = LineageGraph("E", "h", "f")
    with pytest.raises(ValueError, match="unknown parent"):
        g.add(LineageNode(kind="contract", label="orphan", payload={}, parents=["missing"]))


def test_tampering_detected():
    g = LineageGraph("E", "h", "f")
    s = g.add_scenario("s", {"a": 1})
    # simulate tampering: mutate payload after id computed
    object.__getattribute__(s, "payload")["a"] = 999
    ok, problems = g.verify()
    assert not ok
    assert any("hash mismatch" in p for p in problems)


def test_idempotent_append():
    g = LineageGraph("E", "h", "f")
    s1 = g.add_scenario("same-id", {"x": 1})
    s2 = g.add_scenario("same-id", {"x": 1})
    assert s1.node_id == s2.node_id
    assert len([n for n in g.nodes.values() if n.kind == "scenario"]) == 1


def test_content_hash_stable():
    assert content_hash({"b": 1, "a": 2}) == content_hash({"a": 2, "b": 1})
