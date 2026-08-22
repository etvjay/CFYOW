"""Compatibility helper for GenLayer testing-suite contract discovery.

The testing-suite revision required for Bradbury receipt handling currently
recognizes only the AST form ``gl.contract.Contract`` when discovering a
contract by name/path, while official GenLayer contracts use ``gl.Contract``.
This helper avoids modifying canonical contract source: it reads the known
contract file and constructs ContractFactory directly.
"""

from __future__ import annotations

from pathlib import Path

from gltest.contracts.contract_factory import ContractFactory


def contract_factory_from_source(contract_name: str, relative_path: str) -> ContractFactory:
    path = Path(relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"contract source not found: {path}")
    return ContractFactory(
        contract_name=contract_name,
        contract_code=path.read_text(encoding="utf-8"),
    )
