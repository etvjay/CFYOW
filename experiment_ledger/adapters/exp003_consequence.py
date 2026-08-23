"""Deterministic normalization for EXP-003 consequence-stability evidence."""

from __future__ import annotations

from typing import Any


def _int(record: dict[str, Any], key: str) -> int:
    value = record.get(key, 0)
    return int(value or 0)


def normalize_consequence_stability(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    final_judgment_satisfied: bool | None = None,
) -> dict[str, Any]:
    """Compute observed deltas without deciding whether the hypothesis is true.

    `final_judgment_satisfied=None` means no semantic-overturn claim can be made.
    A stale provisional consequence is recorded only when a provisional consequence
    exists and the independently established final judgment is negative.
    """

    before_p = before.get("provisional", {}) or {}
    after_p = after.get("provisional", {}) or {}
    before_s = before.get("settled", {}) or {}
    after_s = after.get("settled", {}) or {}

    before_lineage = before.get("parent_lineage", {}) or {}
    after_lineage = after.get("parent_lineage", {}) or {}

    p_attempt_delta = _int(after_p, "attempts") - _int(before_p, "attempts")
    s_attempt_delta = _int(after_s, "attempts") - _int(before_s, "attempts")
    p_duplicate_delta = _int(after_p, "duplicate_count") - _int(
        before_p, "duplicate_count"
    )
    s_duplicate_delta = _int(after_s, "duplicate_count") - _int(
        before_s, "duplicate_count"
    )
    child_delta = int(after_lineage.get("triggered_transaction_count", 0) or 0) - int(
        before_lineage.get("triggered_transaction_count", 0) or 0
    )

    stale_provisional = None
    if final_judgment_satisfied is not None:
        stale_provisional = bool(after_p.get("applied", False)) and not bool(
            final_judgment_satisfied
        )

    return {
        "schema_version": "cfyow.exp003.consequence-stability.v1",
        "status": "OBSERVED",
        "metrics": {
            "provisional_attempts_before": _int(before_p, "attempts"),
            "provisional_attempts_after": _int(after_p, "attempts"),
            "provisional_attempt_delta": p_attempt_delta,
            "provisional_duplicate_delta": p_duplicate_delta,
            "settled_attempts_before": _int(before_s, "attempts"),
            "settled_attempts_after": _int(after_s, "attempts"),
            "settled_attempt_delta": s_attempt_delta,
            "settled_duplicate_delta": s_duplicate_delta,
            "triggered_child_count_before": int(
                before_lineage.get("triggered_transaction_count", 0) or 0
            ),
            "triggered_child_count_after": int(
                after_lineage.get("triggered_transaction_count", 0) or 0
            ),
            "triggered_child_count_delta": child_delta,
            "provisional_duplicate_observed": p_duplicate_delta > 0,
            "settled_duplicate_observed": s_duplicate_delta > 0,
            "final_judgment_satisfied": final_judgment_satisfied,
            "stale_provisional_consequence_observed": stale_provisional,
        },
        "evidence_boundary": {
            "stale_requires_final_semantic_judgment": True,
            "duplicate_is_not_automatically_harmful": True,
            "idempotent_sink_used": True,
        },
        "interpretation": {
            "status": "UNREVIEWED",
            "claims_supported": [],
            "claims_weakened": [],
        },
    }
