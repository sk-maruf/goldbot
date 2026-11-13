"""S0 feasibility spike: read-only bar download from the MT5 demo terminal (00b prompt).

Refuses unless the attached account is a DEMO account with trading NOT allowed (investor login).
Never logs in, never sends an order, never prints the login number. Output: data/<symbol>_<tf>.parquet
(git-ignored) plus data/provenance.json.
Run: uv run --no-project --python 3.13 --with MetaTrader5 --with pandas --with pyarrow python spikes/feasibility/fetch_bars.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import MetaTrader5 as mt5
import pandas as pd

OUT = Path(__file__).parent / "data"
TIMEFRAMES = {"M5": mt5.TIMEFRAME_M5, "H1": mt5.TIMEFRAME_H1}


def fail(msg: str) -> None:
    mt5.shutdown()
    sys.exit(f"REFUSED: {msg}")


def main() -> None:
    if not mt5.initialize():  # attaches to the running terminal; no credentials passed
        sys.exit(f"REFUSED: cannot attach to terminal: {mt5.last_error()}")
    acc = mt5.account_info()
    if acc is None:
        fail(f"account_info failed: {mt5.last_error()}")
    if acc.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
        fail(f"account trade_mode={acc.trade_mode} is not DEMO")
    # A-72: on Exness-MT5Trial7 trade_allowed stayed True after the user re-logged with the investor
    # password, so this flag may not reveal investor mode. Proceed only on the user's explicit statement.
    user_confirmed = "--user-confirmed-investor-login" in sys.argv
    if acc.trade_allowed and not user_confirmed:
        fail("trading is allowed on this login; log in with the INVESTOR (read-only) password, "
             "or pass --user-confirmed-investor-login if the user states the investor login is active")

    gold = [s.name for s in mt5.symbols_get() if "XAU" in s.name and "USD" in s.name]
    if not gold:
        fail("no XAU*USD symbol visible in this terminal")
    symbol = sorted(gold, key=len)[0]  # plainest name first; every candidate is listed in provenance
    info = mt5.symbol_info(symbol)
    if info is None or not mt5.symbol_select(symbol, True):
        fail(f"symbol_info/select failed for {symbol}")

    OUT.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc)
    prov = {
        "source": "MT5 demo terminal, copy_rates_from_pos newest maxbars-1 bars (read-only)",
        "fetched_utc": now.isoformat(timespec="seconds"),
        "server": acc.server, "account_currency": acc.currency, "account_trade_mode": "DEMO",
        "investor_login": "stated by the user 2026-11-13; account_info().trade_allowed reported "
                          f"{acc.trade_allowed} (A-72)",
        "gold_symbols_visible": gold, "symbol": symbol,
        "symbol_spec": {k: getattr(info, k) for k in (
            "digits", "point", "trade_tick_size", "trade_tick_value", "trade_contract_size",
            "volume_min", "volume_step", "volume_max", "trade_stops_level", "trade_freeze_level",
            "spread_float", "currency_profit", "currency_margin")},
        "files": {},
    }
    for name, tf in TIMEFRAMES.items():
        # shortcut: the newest maxbars-1 bars only (terminal maxbars caps history; settings untouched),
        # raise MT5 'Max bars in chart' if a longer history is ever needed
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, mt5.terminal_info().maxbars - 1)
        if rates is None or len(rates) == 0:
            fail(f"no {name} bars: {mt5.last_error()}")
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)  # MT5 bar time = server time label
        path = OUT / f"{symbol}_{name}.parquet"
        df.to_parquet(path, index=False)
        prov["files"][name] = {"path": path.name, "bars": len(df),
                               "first": str(df["time"].iloc[0]), "last": str(df["time"].iloc[-1])}
        print(f"{name}: {len(df)} bars {df['time'].iloc[0]} .. {df['time'].iloc[-1]}")
    (OUT / "provenance.json").write_text(json.dumps(prov, indent=2, default=str), encoding="utf-8")
    mt5.shutdown()
    print(json.dumps({k: prov[k] for k in ("server", "account_currency", "symbol", "symbol_spec")}, indent=1, default=str))


if __name__ == "__main__":
    main()
