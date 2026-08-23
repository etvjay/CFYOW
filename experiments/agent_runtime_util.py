"""Shared key-loading helper for experiment runners (avoids cross-package imports)."""

from __future__ import annotations

from typing import Any


def load_keys(env_path: str) -> dict[str, str]:
    keys: dict[str, Any] = {}
    with open(env_path) as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                keys[key.strip()] = value.strip().strip('"').strip("'")
    return keys
