"""EXP-003 integration test fixtures and upstream compatibility patches.

The gltest revision used for Bradbury evidence (60f850f) has a latent bug in
``extract_contract_address``: ``"contract_address" in receipt["tx_data_decoded"]``
raises ``TypeError`` when the Bradbury deploy receipt returns
``tx_data_decoded: null`` instead of omitting the key. The fallback branch
(``receipt["data"]["contract_address"]``) is the correct path for Bradbury.
This conftest installs a None-safe shim before any test runs.
"""

from __future__ import annotations

import os
import time as _time

import gltest.utils as _gltest_utils


def _extract_contract_address_none_safe(receipt) -> str:
    tx_data_decoded = receipt.get("tx_data_decoded") if isinstance(receipt, dict) else None
    if isinstance(tx_data_decoded, dict) and "contract_address" in tx_data_decoded:
        return tx_data_decoded["contract_address"]
    data = receipt.get("data") if isinstance(receipt, dict) else None
    if isinstance(data, dict) and "contract_address" in data:
        return data["contract_address"]
    # Bradbury deploy receipts carry the deployed address as `recipient`
    recipient = receipt.get("recipient") if isinstance(receipt, dict) else None
    if recipient:
        return str(recipient)
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


from gltest.contracts.contract_factory import ContractFactory as _CF
from gltest.exceptions import DeploymentError as _DE

_CAPACITY_RETRY_ENV = "EXP003_DEPLOY_RETRIES"


def _install_capacity_retry() -> None:
    """Retry contract deploys when Bradbury rejects with gas rate limit (-32005)."""
    if getattr(_CF, "_cfyow_capacity_retry", False):
        return
    original = _CF.deploy

    def deploy_with_retry(self, *args, **kwargs):
        attempts = int(os.getenv(_CAPACITY_RETRY_ENV, "8"))
        delay_s = float(os.getenv("EXP003_DEPLOY_RETRY_DELAY_S", "2"))
        last_exc = None
        for attempt in range(max(1, attempts)):
            try:
                return original(self, *args, **kwargs)
            except (_DE, Exception) as exc:
                message = str(exc)
                if "-32005" not in message and "capacity" not in message.lower():
                    raise
                last_exc = exc
                _time.sleep(delay_s * (attempt + 1))
        raise last_exc

    deploy_with_retry.__doc__ = original.__doc__
    _CF.deploy = deploy_with_retry
    _CF._cfyow_capacity_retry = True


_install_capacity_retry()
