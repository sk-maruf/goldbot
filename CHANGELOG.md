# Changelog

All notable changes to GoldBot. Milestone evidence lives in `docs/STATUS.md`.

## M1 Foundation (2026-11-14)

### Added
- Decimal money core: single MT5 float boundary (`core/convert.py`), currency-safe `Money`
  (`core/money.py`), conservative rounding and OFF_TICK rejection (`core/rounding.py`).
- Clocks and SNTP offset check (`core/clock.py`, `core/ntp.py`).
- Structured JSON logs with secret redaction (`core/logs.py`); keyring-only secrets (`core/secrets.py`).
- Append-only SHA-256 audit chain in SQLite with tamper, env and store-integrity checks (`core/audit.py`).
- Config loading and validation with fail-closed startup gates (`config.py`), env-separated databases
  (`envguard.py`), Phase-0 clearance check (`phase0.py`), `goldbot doctor` CLI (`cli.py`), Pydantic
  models synced with JSON schemas (`models/`).
- `BrokerPort` protocol and a deterministic, ILLUSTRATIVE `FakeBroker` with MT5-style request validation.
- CI on Windows and Linux (ruff, pyright, pytest with coverage, test-plan check, gitleaks), actions
  pinned to commit SHAs.
