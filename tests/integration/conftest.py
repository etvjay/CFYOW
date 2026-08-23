"""EXP-003 integration test fixtures and upstream compatibility patches.

The gltest revision used for Bradbury evidence (60f850f) has a latent bug in
``extract_contract_address``: ``"contract_address" in receipt["tx_data_decoded"]``
raises ``TypeError`` when the Bradbury deploy receipt returns
``tx_data_decoded: null`` instead of omitting the key. The fallback branch
(``receipt["data"]["contract_address"]``) is the correct path for Bradbury.
This conftest installs a None-safe shim before any test runs.
"""

from __future__ import annotations

import gltest.utils as _gltest_utils


def _extract_contract_address_none_safe(receipt) -> str:
    tx_data_decoded = receipt.get("tx_data_decoded") if isinstance(receipt, dict) else None
    if isinstance(tx_data_decoded, dict) and "contract_address" in tx_data_decoded:
        return tx_data_decoded["contract_address"]
    data = receipt.get("data") if isinstance(receipt, dict) else None
    if isinstance(data, dict) and "contract_address" in data:
        return data["contract_address"]
    raise ValueError("Transaction receipt missing contract address")


_extract_contract_address_none_safe.__doc__ = _gltest_utils.extract_contract_address.__doc__
_gltest_utils.extract_contract_address = _extract_contract_address_none_safe

# Also patch the reference imported inside contract_factory (it binds by value at import time).
try:  # pragma: no cover - import shape varies across gltest revisions
    import gltest.contracts.contract_factory as _factory_mod

    if hasattr(_factory_mod, "extract_contract_address"):
        _factory_mod.extract_contract_address = _extract_contract_address_none_safe
except ImportError:
    pass
