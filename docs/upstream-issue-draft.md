# Upstream Issue Draft — genlayer-testing-suite / genlayer-py (INTERNAL, DO NOT FILE YET)

**Status:** internal draft. Keep in repo until we decide to publish; remove if strategy changes.
**Environment:** GenLayer Bradbury testnet (chain 4221), Python 3.12, gltest + genlayer-py pinned per matrix below.

## Summary

There is currently **no released combination of genlayer-test and genlayer-py that can both deploy contracts and parse receipts on Bradbury testnet**. We isolated six distinct failures across the tooling matrix while building EXP-003 evidence capture (repo: etvjay/CFYOW). Each was confirmed by independent CI runs.

## Tooling matrix observed

| gltest | genlayer-py | deploy | receipt parse | notes |
|---|---|---|---|---|
| v0.29 | v0.18 | OK (tx accepted, status 5) | FAIL — no status `14`, Studio-only receipt shape | direct-mode works |
| 60f850f (#91) | main head dd25ef7 | deploy tx reverts on-chain | partial | fee kwargs mismatch with live consensus contract |
| 60f850f (#91) | v0.19 line ec7cab9 | deploy tx reverts on-chain | OK shape-wise | same revert; unrelated to fees kwarg (none passed) |

## Individual defects

1. **`extract_contract_address` TypeError** (gltest @60f850f, `gltest/utils.py`): `"contract_address" in receipt["tx_data_decoded"]` raises `TypeError` when Bradbury returns `tx_data_decoded: null`. Needs None-guard before fallback to `receipt["data"]["contract_address"]`.

2. **Deploy receipts lack contract address entirely** on Bradbury: neither `tx_data_decoded.contract_address` nor `data.contract_address` present; deployed address only appears as top-level `recipient`. Suggest documenting/normalizing this shape.

3. **Unknown transaction status `14`**: Bradbury emits status 14 (`LEADER_REVEALING` exists only on genlayer-py main, unreleased). v0.18's `TRANSACTION_STATUS_NUMBER_TO_NAME` raises `KeyError: '14'` during receipt parsing.

4. **Testnet receipt shape unsupported by v0.29 `tx_execution_succeeded`**: requires `consensus_data.leader_receipt[0].execution_result == "SUCCESS"`; Bradbury returns flat receipts with `status: 5 / ACCEPTED`, `result: AGREE`, `tx_execution_result: FINISHED_WITH_RETURN`. Fixed in #91 but #91 is unreleased.

5. **Direct-mode calldata regression** (commit `2ff9d07`, in all post-v0.29 revisions): constructor/method args roundtripped through calldata encode/decode raise `DecodingError: unexpected end of memory` for contracts using `TreeMap[str, ...]` storage and `Address` args. Breaks all our direct-mode tests.

6. **Read calls fail without explicit account** (gltest @60f850f): `ContractFactory.deploy()` without explicit account builds Contract with `account=None`; subsequent view call raises `GenLayerError: No account provided and no account is connected` instead of falling back to default account.

7. **No retry handling for gas rate limiting**: Bradbury frequently returns `-32005 transaction gas rate limit exceeded: node is at capacity`; deploys fail hard with no built-in backoff.

## Workarounds we ship (for reference)

- None-safe address extraction + `recipient` fallback shim
- Tuple-tolerant message normalization in child-lineage capture
- Default-account injection after build
- Deploy retry with linear backoff on `-32005`
- Dual pins: v0.29 for unit/direct CI, 60f850f+ec7cab9 for network integration

## Ask

- Released tag pairing a gltest revision with the genlayer-py version it actually targets
- Status `14` in a released genlayer-py
- Testnet deploy revert diagnosis: identical contract code deploys fine on v0.29 stack, reverts on v0.19 line (tx example available)
