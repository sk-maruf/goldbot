"""SEC-001/SEC-004: keyring wrapper (in-memory backend only, never the real Credential Manager)."""

from __future__ import annotations

from collections.abc import Iterator

import keyring
import pytest
from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError

from goldbot.core import secrets
from goldbot.core.logs import REDACTED, redact


class MemoryKeyring(KeyringBackend):
    priority = 1  # type: ignore[assignment]

    def __init__(self) -> None:
        super().__init__()
        self.store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        if self.store.pop((service, username), None) is None:
            raise PasswordDeleteError(username)


@pytest.fixture
def memory() -> Iterator[MemoryKeyring]:
    previous = keyring.get_keyring()
    backend = MemoryKeyring()
    keyring.set_keyring(backend)
    yield backend
    keyring.set_keyring(previous)


def test_sec_001_set_get_delete_round_trip_under_service_goldbot(memory: MemoryKeyring) -> None:
    secrets.set_secret("mt5_investor_password", "inv-pass-1")
    assert memory.store == {("goldbot", "mt5_investor_password"): "inv-pass-1"}
    assert secrets.get_secret("mt5_investor_password") == "inv-pass-1"
    secrets.delete_secret("mt5_investor_password")
    assert secrets.get_secret("mt5_investor_password") is None


def test_missing_secret_is_none(memory: MemoryKeyring) -> None:
    assert secrets.get_secret("absent") is None


def test_deleting_a_missing_secret_raises(memory: MemoryKeyring) -> None:
    with pytest.raises(PasswordDeleteError):
        secrets.delete_secret("absent")


def test_sec_004_value_read_from_keyring_is_registered_with_the_redactor(memory: MemoryKeyring) -> None:
    memory.store[("goldbot", "api")] = "read-back-secret-77"  # stored by another process
    assert redact("x read-back-secret-77") != f"x {REDACTED}"
    secrets.get_secret("api")
    assert redact("x read-back-secret-77") == f"x {REDACTED}"


def test_sec_004_value_written_to_keyring_is_registered_with_the_redactor(memory: MemoryKeyring) -> None:
    secrets.set_secret("totp", "written-secret-55")
    assert redact("written-secret-55") == REDACTED


@pytest.mark.parametrize(("name", "value"), [("", "v"), ("n", "")])
def test_empty_name_or_value_is_rejected(memory: MemoryKeyring, name: str, value: str) -> None:
    with pytest.raises(ValueError, match="empty"):
        secrets.set_secret(name, value)
    assert memory.store == {}


def test_empty_name_is_rejected_on_read_and_delete(memory: MemoryKeyring) -> None:
    with pytest.raises(ValueError, match="empty"):
        secrets.get_secret("")
    with pytest.raises(ValueError, match="empty"):
        secrets.delete_secret("")
