"""OS-keyring access for C4 secrets (SEC-001), service ``goldbot``.

Every value read or written is registered with the log redactor first (SEC-004). Nothing here
logs; keyring errors propagate so callers fail closed.
"""

from __future__ import annotations

import keyring

from goldbot.core.logs import register_secret

SERVICE = "goldbot"


def _require(label: str, text: str) -> None:
    if not text:
        raise ValueError(f"secret {label} must not be empty")


def get_secret(name: str) -> str | None:
    _require("name", name)
    value = keyring.get_password(SERVICE, name)
    if value:
        register_secret(value)
    return value


def set_secret(name: str, value: str) -> None:
    _require("name", name)
    _require("value", value)
    register_secret(value)
    keyring.set_password(SERVICE, name, value)


def delete_secret(name: str) -> None:
    _require("name", name)
    keyring.delete_password(SERVICE, name)
