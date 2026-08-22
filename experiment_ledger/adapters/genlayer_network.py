"""GenLayer network evidence capture for Experiment Ledger v1.

This adapter records only node-observable facts. It does not infer hidden model
reasoning or reconstruct validator semantics from hashes.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import requests

TERMINAL_STATUSES = {
    "FINALIZED",
    "CANCELED",
    "UNDETERMINED",
    "VALIDATORS_TIMEOUT",
    "LEADER_TIMEOUT",
}

APPEAL_STATUSES = {"APPEAL_REVEALING", "APPEAL_COMMITTING"}


@dataclass
class JsonRpcClient:
    url: str
    timeout_s: float = 15.0
    session: Any = requests

    def call(self, method: str, params: list[Any]) -> Any:
        response = self.session.post(
            self.url,
            json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
            timeout=self.timeout_s,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise RuntimeError(f"GenLayer RPC {method} failed: {payload['error']}")
        return payload.get("result")

    def transaction_status(self, tx_hash: str) -> dict[str, Any]:
        result = self.call("gen_getTransactionStatus", [{"txId": tx_hash}])
        if not isinstance(result, dict):
            raise RuntimeError("unexpected gen_getTransactionStatus response")
        return result

    def transaction_receipt(self, tx_hash: str) -> dict[str, Any]:
        result = self.call("gen_getTransactionReceipt", [{"txId": tx_hash}])
        if not isinstance(result, dict):
            raise RuntimeError("unexpected gen_getTransactionReceipt response")
        return result

    def contract_state(self, address: str, status: str) -> str:
        return self.call(
            "gen_getContractState",
            [{"address": address, "status": status.lower()}],
        )


def summarize_rounds(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize consensus round metadata exposed by the public receipt API."""
    normalized: list[dict[str, Any]] = []
    for raw in receipt.get("roundData", []) or []:
        validators = list(raw.get("roundValidators", []) or [])
        result_hashes = list(raw.get("validatorResultHash", []) or [])
        vote_hashes = list(raw.get("validatorVotesHash", []) or [])
        normalized.append(
            {
                "round": raw.get("round"),
                "leader_index": raw.get("leaderIndex"),
                "votes_committed": raw.get("votesCommitted"),
                "votes_revealed": raw.get("votesRevealed"),
                "appeal_bond": raw.get("appealBond"),
                "rotations_left": raw.get("rotationsLeft"),
                "result": raw.get("result"),
                "validator_count": len(validators),
                "validators": validators,
                "validator_vote_hashes": vote_hashes,
                "validator_result_hashes": result_hashes,
            }
        )
    return normalized


def derive_consensus_observations(
    history: list[dict[str, Any]], receipt: dict[str, Any]
) -> dict[str, Any]:
    statuses = [item.get("status") for item in history]
    rounds = summarize_rounds(receipt)
    appeal_observed = any(status in APPEAL_STATUSES for status in statuses)
    appeal_timestamp = (receipt.get("timestamps") or {}).get("AppealSubmitted", 0)
    if appeal_timestamp:
        appeal_observed = True

    return {
        "status_path": statuses,
        "accepted_observed": "ACCEPTED" in statuses,
        "finalized_observed": "FINALIZED" in statuses,
        "appeal_observed": appeal_observed,
        "round_count": len(rounds),
        "reexecution_or_additional_round_observed": len(rounds) > 1,
        "initial_validator_count": receipt.get("numOfInitialValidators"),
        "rounds": rounds,
        "tx_execution_hash": receipt.get("txExecutionHash"),
        "transaction_result_code": receipt.get("result"),
        "unavailable": [
            "validator_private_reasoning",
            "validator_prompt_context",
            "semantic meaning of validator result hashes without trace data",
        ],
    }


def capture_transaction_lifecycle(
    rpc_url: str,
    tx_hash: str,
    *,
    contract_address: str | None = None,
    poll_interval_s: float = 1.0,
    max_polls: int = 180,
    client: JsonRpcClient | None = None,
) -> dict[str, Any]:
    """Capture a GenLayer transaction from current status through a terminal state.

    The function can start after submission; it records every distinct status seen.
    If polling begins after ACCEPTED has already passed, `accepted_observed` remains
    false rather than inferring that state from finalization.
    """
    rpc = client or JsonRpcClient(rpc_url)
    history: list[dict[str, Any]] = []
    last_status: str | None = None

    for _ in range(max_polls):
        observed_at_ns = time.time_ns()
        current = rpc.transaction_status(tx_hash)
        status = current.get("status")
        if status != last_status:
            history.append(
                {
                    "status": status,
                    "status_code": current.get("statusCode"),
                    "observed_at_ns": observed_at_ns,
                }
            )
            last_status = status
        if status in TERMINAL_STATUSES:
            break
        time.sleep(poll_interval_s)
    else:
        return {
            "status": "INVALID_RUN",
            "failure": {
                "type": "POLL_TIMEOUT",
                "message": f"transaction did not reach a terminal status after {max_polls} polls",
            },
            "transaction_hash": tx_hash,
            "history": history,
        }

    receipt = rpc.transaction_receipt(tx_hash)
    evidence: dict[str, Any] = {
        "status": "SUCCESS",
        "transaction_hash": tx_hash,
        "history": history,
        "receipt": receipt,
        "consensus": derive_consensus_observations(history, receipt),
        "state_snapshots": {},
    }

    if contract_address:
        for state_status in ("accepted", "finalized"):
            try:
                evidence["state_snapshots"][state_status] = rpc.contract_state(
                    contract_address, state_status
                )
            except Exception as exc:
                evidence["state_snapshots"][state_status] = {
                    "unavailable": True,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }

    return evidence
