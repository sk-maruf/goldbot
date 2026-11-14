"""Currency-tagged money (TRADING_RISK_SPEC RISK-023, DATA-004, CENT-011)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, get_args

from goldbot.core.convert import DECIMAL_CONTEXT, parse_decimal, require_decimal

Currency = Literal["USC", "USD"]
_CURRENCIES: tuple[str, ...] = get_args(Currency)
USC_PER_USD = 100  # CENT_ACCOUNT_VALIDATION CENT-012 [REPORTED S4]; display conversion only


class CurrencyMismatchError(ValueError):
    """Arithmetic or ordering across currencies (RISK-023, GV-06)."""


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        require_decimal(self.amount, "amount")
        if self.currency not in _CURRENCIES:
            raise ValueError(f"unknown currency {self.currency!r}; expected one of {_CURRENCIES}")

    def _same(self, other: object) -> Money:
        if not isinstance(other, Money):
            raise TypeError(f"Money cannot be combined with {type(other).__name__}")
        if other.currency != self.currency:
            raise CurrencyMismatchError(f"cannot combine {self.currency} with {other.currency}")
        return other

    def __add__(self, other: Money) -> Money:
        return Money(DECIMAL_CONTEXT.add(self.amount, self._same(other).amount), self.currency)

    def __sub__(self, other: Money) -> Money:
        return Money(DECIMAL_CONTEXT.subtract(self.amount, self._same(other).amount), self.currency)

    def __neg__(self) -> Money:
        return Money(DECIMAL_CONTEXT.minus(self.amount), self.currency)

    def __lt__(self, other: Money) -> bool:
        return self.amount < self._same(other).amount

    def __le__(self, other: Money) -> bool:
        return self.amount <= self._same(other).amount

    def __gt__(self, other: Money) -> bool:
        return self.amount > self._same(other).amount

    def __ge__(self, other: Money) -> bool:
        return self.amount >= self._same(other).amount

    def to_json(self) -> dict[str, str]:
        """DATA-004 form: decimal string (never exponent notation) plus currency."""
        return {"amount": format(self.amount, "f"), "currency": self.currency}

    @classmethod
    def from_json(cls, data: Mapping[str, object]) -> Money:
        if set(data) != {"amount", "currency"}:
            raise ValueError(f"money JSON needs exactly amount and currency, got {sorted(data)}")
        currency = data["currency"]
        if currency not in _CURRENCIES:
            raise ValueError(f"unknown currency {currency!r}; expected one of {_CURRENCIES}")
        return cls(parse_decimal(data["amount"], "amount"), currency)  # type: ignore[arg-type]


def convert_display(money: Money, *, rate_source: Literal["ACCOUNT_DEFINITION"]) -> Money:
    """USC <-> USD for labelled display only; never used inside the RiskEngine (RISK-023)."""
    if rate_source != "ACCOUNT_DEFINITION":
        raise ValueError(f"rate_source must be ACCOUNT_DEFINITION, got {rate_source!r}")
    if money.currency == "USC":
        return Money(DECIMAL_CONTEXT.divide(money.amount, USC_PER_USD), "USD")
    return Money(DECIMAL_CONTEXT.multiply(money.amount, USC_PER_USD), "USC")
