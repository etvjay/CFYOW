"""Appeal helpers for GenLayer network experiments.

The Experiment Ledger never guesses an appeal bond. By default it asks the
connected GenLayer client for the protocol minimum. An explicit positive override
is supported only for controlled debugging/reproduction.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class AppealBondResolution:
    value: int
    source: str
    minimum_bond: int
    can_appeal: bool | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_appeal_bond(
    client: Any,
    transaction_id: str,
    *,
    override: str | int | None = None,
) -> AppealBondResolution:
    """Return the bond to use for an appeal without silently defaulting to zero.

    `override` must be a positive integer when provided. Otherwise the minimum
    bond is fetched through `client.get_min_appeal_bond(transaction_id=...)`.
    `client.can_appeal(...)` is recorded when available but does not replace the
    network's bond calculation.
    """
    can_appeal: bool | None = None
    if hasattr(client, "can_appeal"):
        can_appeal = bool(client.can_appeal(transaction_id=transaction_id))

    if override is not None and str(override).strip() != "":
        value = int(override)
        if value <= 0:
            raise ValueError("explicit appeal bond override must be positive")

        if not hasattr(client, "get_min_appeal_bond"):
            raise RuntimeError("GenLayer client does not expose get_min_appeal_bond")
        minimum = int(client.get_min_appeal_bond(transaction_id=transaction_id))
        if minimum < 0:
            raise RuntimeError("network returned a negative minimum appeal bond")
        if value < minimum:
            raise ValueError(
                f"explicit appeal bond {value} is below network minimum {minimum}"
            )
        return AppealBondResolution(
            value=value,
            source="explicit_override",
            minimum_bond=minimum,
            can_appeal=can_appeal,
        )

    if not hasattr(client, "get_min_appeal_bond"):
        raise RuntimeError("GenLayer client does not expose get_min_appeal_bond")

    minimum = int(client.get_min_appeal_bond(transaction_id=transaction_id))
    if minimum < 0:
        raise RuntimeError("network returned a negative minimum appeal bond")

    return AppealBondResolution(
        value=minimum,
        source="network_minimum",
        minimum_bond=minimum,
        can_appeal=can_appeal,
    )
