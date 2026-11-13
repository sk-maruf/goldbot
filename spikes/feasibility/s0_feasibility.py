"""S0 feasibility spike (prompts/00b). PT0 — FEASIBILITY ONLY, NOT A RESULT (BT-001).

Throwaway code: src/goldbot never imports it. No MT5 calls: it reads the parquet bars in data/.
It computes stop distances, spreads and sizing only. It never computes P/L, win rate,
expectancy or returns (RES-021). Every constant below was fixed before any output was seen (C1).

Run: uv run --no-project --python 3.13 --with pandas --with pyarrow --with numpy \
         python spikes/feasibility/s0_feasibility.py
"""

from __future__ import annotations

import json
import math
from collections import Counter
from decimal import ROUND_DOWN, ROUND_UP, Decimal
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out"
LABEL = "PT0 — FEASIBILITY ONLY, NOT A RESULT"
UTC, NY, LON = "UTC", "America/New_York", "Europe/London"

# ---- Fixture equity and the ILL-CENT profile (CENT_ACCOUNT_VALIDATION §4) ----
EQUITY = Decimal("10000.00")  # USC, fixture; held constant because no P/L is computed
TICK_SIZE, TICK_VALUE = Decimal("0.01"), Decimal("1.00")  # ILL-CENT, USC per 1.00 lot
USC_PER_USD_LOT = TICK_VALUE / TICK_SIZE  # 100 USC per $1 move per 1.00 lot
VOL_MIN = VOL_STEP = Decimal("0.01")
P01_LEVELS = ("0.10", "0.25", "0.50")  # recommended range; none of them is an approval
P09, P10, P11 = Decimal("1.0"), Decimal("10"), Decimal("1000")
# ILLUSTRATIVE substitutes for order_calc_margin / account_info (not available offline; BLOCKED to M2)
ILL_LEVERAGE = Decimal("200")  # margin = notional / 200 (the P-12 cap value)
ILL_SO_LEVEL = Decimal("100")  # margin_so_so %, a conservative stand-in
POINT_USD = 0.001  # XAUUSDm point; bar spread column is in points

A10_CODES = ("MIN_VOLUME_EXCEEDS_BUDGET", "EFFECTIVE_LEVERAGE", "MARGIN_UTILISATION",
             "MARGIN_LEVEL", "FREE_MARGIN", "STOP_OUT_DISTANCE", "AGGREGATE_RISK", "SPREAD_TOO_WIDE")
EXCLUDED_CODES = ("OUTSIDE_STRATEGY_ENVELOPE", "PRE_CLOSE", "CALC_UNAVAILABLE")


# ---------------------------------------------------------------- sizing (RISK-010..013, EXP-003..006)
def dec(x: float) -> Decimal:
    return Decimal(repr(round(float(x), 6)))


def risk_engine(budget: Decimal, d_usd: Decimal, slip_usd: Decimal, price: Decimal,
                slot_busy: bool = False) -> tuple[str | None, Decimal]:
    """Return (rejection code or None, volume) for one signal under ILL-CENT."""
    loss_lot = d_usd * USC_PER_USD_LOT  # RISK-011 via the RISK-014 formula
    slip_lot = slip_usd * USC_PER_USD_LOT  # RISK-012
    vol = (budget / (loss_lot + slip_lot) / VOL_STEP).to_integral_value(ROUND_DOWN) * VOL_STEP
    if vol < VOL_MIN:
        return "MIN_VOLUME_EXCEEDS_BUDGET", vol
    if (vol * (loss_lot + slip_lot)).quantize(Decimal("0.01"), ROUND_UP) > budget:
        return "BUDGET_CHECK_FAILED", vol
    if slot_busy:  # one slot, P-31 = P-01: any open position fails RISK-015
        return "AGGREGATE_RISK", vol
    notional = vol * price * USC_PER_USD_LOT  # EXP-002 formula cross-check form
    if notional / EQUITY > P09:
        return "EFFECTIVE_LEVERAGE", vol
    required = notional / ILL_LEVERAGE  # ILLUSTRATIVE stand-in for order_calc_margin
    if required / EQUITY * 100 > P10:
        return "MARGIN_UTILISATION", vol
    if EQUITY / required * 100 < P11:
        return "MARGIN_LEVEL", vol
    if EQUITY - required <= 0:
        return "FREE_MARGIN", vol
    if (EQUITY - ILL_SO_LEVEL / 100 * required) / (vol * USC_PER_USD_LOT) < 3 * d_usd:
        return "STOP_OUT_DISTANCE", vol
    return None, vol


def budget_for(p01: str) -> Decimal:
    return (EQUITY * Decimal(p01) / 100).quantize(Decimal("0.01"), ROUND_DOWN)


def _self_check() -> None:
    """Hand-computed cases (CGV-01, CGV-06, TRADING_RISK_SPEC §3.1, STRATEGY_CANDIDATES §2.2)."""
    b, s, p = budget_for("0.25"), Decimal("0.30"), Decimal("4070")
    assert b == Decimal("25.00")
    assert risk_engine(b, Decimal("24"), s, p) == (None, Decimal("0.01"))  # loss 24.30 USC
    assert risk_engine(b, Decimal("25"), s, p)[0] == "MIN_VOLUME_EXCEEDS_BUDGET"  # §3.1
    assert risk_engine(b, Decimal("10"), s, p) == (None, Decimal("0.02"))  # loss 20.60 USC
    assert risk_engine(b, Decimal("8"), s, p) == ("EFFECTIVE_LEVERAGE", Decimal("0.03"))
    assert risk_engine(b, Decimal("5"), s, p) == ("EFFECTIVE_LEVERAGE", Decimal("0.04"))
    assert risk_engine(Decimal("22.50"), Decimal("24"), s, p)[0] == "MIN_VOLUME_EXCEEDS_BUDGET"
    assert risk_engine(b, Decimal("15"), s, p, slot_busy=True)[0] == "AGGREGATE_RISK"
    assert risk_engine(b, Decimal("30"), s, p, slot_busy=True)[0] == "MIN_VOLUME_EXCEEDS_BUDGET"


# ---------------------------------------------------------------- data helpers
def holdout_cut(t: pd.Series) -> pd.Timestamp:
    """RES-005: holdout = the larger of 6 months and 20% (by time span or by bar count)."""
    first, last = t.iloc[0], t.iloc[-1]
    cands = [last - pd.DateOffset(months=6), last - 0.2 * (last - first),
             t.iloc[math.ceil(0.8 * len(t))]]
    return min(cands).floor("D")


def resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    r = df.set_index("time").resample(rule, label="left", closed="left").agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"),
        tick_volume=("tick_volume", "sum"), spread=("spread", "last")).dropna(subset=["open"])
    return r.reset_index()


def prep(df: pd.DataFrame, tf: pd.Timedelta) -> pd.DataFrame:
    """ATR(14) Wilder, close time, module-1 trend (20 bars, strength >= 0.5), spread in USD."""
    df = df.reset_index(drop=True).copy()
    pc = df.close.shift()
    tr = pd.concat([df.high - df.low, (df.high - pc).abs(), (df.low - pc).abs()], axis=1).max(axis=1)
    df["atr"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
    df.loc[:13, "atr"] = np.nan
    ret = df.close - df.close.shift(20)
    strength = ret.abs() / (df.atr * math.sqrt(20))
    df["trend"] = np.where(strength >= 0.5, np.sign(ret), 0)
    df["ctime"] = df.time + tf
    df["spr"] = df.spread * POINT_USD
    return df


def add_cost_context(df: pd.DataFrame) -> pd.DataFrame:
    """P-13 B / P-26 median: rolling 20-day median spread, same server hour, strictly before the bar.
    Liquidity proxy: tick_volume >= 20th percentile for the same server hour on this (pre-cut) split."""
    s = df.set_index("time")["spr"]
    med = s.groupby(s.index.hour, group_keys=False).apply(
        lambda g: g.rolling("20D", closed="left").median()).sort_index()
    df["med20"] = med.to_numpy()
    df.loc[df.time < df.time.iloc[0] + pd.Timedelta(days=20), "med20"] = np.nan
    q20 = df.groupby(df.time.dt.hour).tick_volume.quantile(0.2)
    df["liquid"] = df.tick_volume.to_numpy() >= q20.reindex(df.time.dt.hour).to_numpy()
    return df


def asof(htf: pd.DataFrame, col: str, t: pd.Timestamp):
    """Value of the last higher-timeframe bar closed at or before t (MI-034)."""
    i = htf.ctime.searchsorted(t, side="right") - 1
    return htf[col].iat[i] if i >= 0 else np.nan


def swings(high: np.ndarray, low: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """MI-030 swing flags at bar i (confirmed at the close of bar i+k)."""
    n = len(high)
    sh, sl = np.zeros(n, bool), np.zeros(n, bool)
    for i in range(k, n - k):
        sh[i] = high[i] > high[i - k:i].max() and high[i] >= high[i + 1:i + k + 1].max()
        sl[i] = low[i] < low[i - k:i].min() and low[i] <= low[i + 1:i + k + 1].min()
    return sh, sl


def pin(o, h, l, c, d, atr) -> bool:
    """Rejection candle = MI-031 pin bar geometry with the MI-031 range >= 0.3 ATR filter."""
    rng = h - l
    if not rng > 0 or not rng >= 0.3 * atr:
        return False
    wick = (min(o, c) - l) if d > 0 else (h - max(o, c))
    return wick >= 2 / 3 * rng


def ny_minutes(t: pd.Timestamp) -> tuple[int, int]:
    ny = t.tz_convert(NY)
    return ny.weekday(), ny.hour * 60 + ny.minute


def session_of(t: pd.Timestamp) -> str | None:
    """G4 gap reading: London = 08:00-17:00 Europe/London, New York = 08:00-17:00 America/New_York;
    New York wins in the overlap."""
    for name, tz in (("NY", NY), ("LON", LON)):
        loc = t.tz_convert(tz)
        if 8 * 60 <= loc.hour * 60 + loc.minute < 17 * 60:
            return name
    return None


def pre_close(t: pd.Timestamp, max_hold: int) -> bool:
    """P-19 and the §2.1 entry cut-off (t + max_hold <= P-33). Daily break taken as 16:58 New York
    (S2's 20:58 GMT+0, moving with US DST as the bars show); Friday is the week's last session."""
    wd, m = ny_minutes(t)
    deadline, p19 = (15 * 60 + 58, 14 * 60 + 58) if wd == 4 else (16 * 60 + 28, 15 * 60 + 58)
    return m >= p19 or m + max_hold > deadline


def setup(df: pd.DataFrame, j: int, d: int, d_usd: float, session: str | None, **extra) -> dict:
    t = df.ctime.iat[j]
    return dict(t=t, dir=d, price=df.close.iat[j] + (df.spr.iat[j] if d > 0 else 0.0), D=d_usd,
                spr=df.spr.iat[j], med20=df.med20.iat[j], liquid=bool(df.liquid.iat[j]),
                session=session, day=t.tz_convert(NY).date(), **extra)


# ---------------------------------------------------------------- candidate A
def candidate_a(m5: pd.DataFrame, m15: pd.DataFrame, h1: pd.DataFrame, diag: Counter) -> list[dict]:
    out = []
    days = sorted(set(m5.time.dt.tz_convert(LON).dt.date))
    for day in days:
        for sess, tz, (sh, smin) in (("LON", LON, (8, 0)), ("NY", NY, (9, 30))):
            start = pd.Timestamp(f"{day} {sh:02d}:{smin:02d}", tz=tz).tz_convert(UTC)
            end = start + pd.Timedelta(hours=1)
            rng = m15[(m15.time >= start) & (m15.time < end)]
            if len(rng) != 4:
                continue
            diag["ranges"] += 1
            hi, lo = rng.high.max(), rng.low.min()
            mid, atr_h1 = (hi + lo) / 2, asof(h1, "atr", end)
            if not (hi - lo) >= 0.3 * atr_h1:
                diag["range_too_narrow"] += 1
                continue
            # G1 break with displacement (MI-030: <=3 same-direction candles, body >= 1.5 ATR, ratio >= 0.6)
            k0 = int(m15.time.searchsorted(end))
            brk = None
            for k in range(k0, len(m15)):
                if m15.ctime.iat[k] > end + pd.Timedelta(minutes=120):
                    break
                c = m15.close.iat[k]
                d = 1 if c > hi else -1 if c < lo else 0
                if d and has_displacement(m15, k, d):
                    brk = (k, d)
                    break
            if brk is None:
                continue
            diag["breaks"] += 1
            k, d = brk
            band, level = 0.1 * m15.atr.iat[k], hi if d > 0 else lo
            j0 = int(m5.time.searchsorted(m15.ctime.iat[k]))
            for j in range(j0, min(j0 + 12, len(m5))):  # G4 retest within 12 M5 bars
                tj = m5.ctime.iat[j]
                closed = m15.iloc[k + 1:k + 9]
                closed = closed[closed.ctime <= tj]
                if ((closed.close - mid) * d < 0).any():  # M15 close back beyond the midpoint
                    diag["invalidated"] += 1
                    break
                o, h, l_, c = m5.open.iat[j], m5.high.iat[j], m5.low.iat[j], m5.close.iat[j]
                touched = l_ <= level + band if d > 0 else h >= level - band
                if touched and (c - level) * d > 0 and pin(o, h, l_, c, d, m5.atr.iat[j]):
                    if asof(h1, "trend", tj) == -d:  # G6 gate
                        diag["no_trade_regime"] += 1
                        break
                    spr = m5.spr.iat[j]
                    sl = mid - spr if d > 0 else mid + spr
                    entry = c + spr if d > 0 else c
                    out.append(setup(m5, j, d, abs(entry - sl), sess))
                    diag["setups"] += 1
                    break
    return out


def has_displacement(df: pd.DataFrame, k: int, d: int) -> bool:
    for n in (1, 2, 3):
        leg = df.iloc[k - n + 1:k + 1]
        if len(leg) < n or not ((leg.close - leg.open) * d > 0).all():
            return False
        body, rng = (leg.close - leg.open).abs().sum(), (leg.high - leg.low).sum()
        if body >= 1.5 * df.atr.iat[k] and rng > 0 and body / rng >= 0.6:
            return True
    return False


# ---------------------------------------------------------------- candidate B
def candidate_b(h1: pd.DataFrame, h4: pd.DataFrame, diag: Counter) -> list[dict]:
    out = []
    sh, sl = swings(h1.high.to_numpy(), h1.low.to_numpy(), 2)
    swing_hi = swing_lo = None  # [level, consumed]
    for j in range(len(h1)):
        c, t = h1.close.iat[j], h1.ctime.iat[j]
        for d, sw in ((1, swing_hi), (-1, swing_lo)):
            if sw and not sw[1] and (c - sw[0]) * d > 0:  # G1 BOS: first close beyond the swing
                sw[1] = True
                diag["bos"] += 1
                if asof(h4, "trend", t) != d:  # G6 H4 trend in the BOS direction
                    continue
                sess = session_of(t)
                if sess is None or np.isnan(h1.atr.iat[j]):
                    continue
                out.append(setup(h1, j, d, 1.5 * h1.atr.iat[j] + h1.spr.iat[j], sess))
                diag["setups"] += 1
        if j >= 2 and sh[j - 2]:
            swing_hi = [h1.high.iat[j - 2], False]
        if j >= 2 and sl[j - 2]:
            swing_lo = [h1.low.iat[j - 2], False]
    return out


# ---------------------------------------------------------------- candidate C
def candidate_c(m5: pd.DataFrame, m15: pd.DataFrame, h1: pd.DataFrame, diag: Counter) -> list[dict]:
    out = []
    o, h, l_, c, atr = (m5[x].to_numpy() for x in ("open", "high", "low", "close", "atr"))
    sh, sl = swings(h, l_, 2)
    xh, xl = swings(m15.high.to_numpy(), m15.low.to_numpy(), 5)  # external swings for P/D
    conf_t = m15.ctime.shift(-5)  # confirmed at the close of bar i+5
    ext_hi = pd.DataFrame({"ctime": conf_t[xh], "v": m15.high[xh]}).dropna().reset_index(drop=True)
    ext_lo = pd.DataFrame({"ctime": conf_t[xl], "v": m15.low[xl]}).dropna().reset_index(drop=True)
    pool = {1: None, -1: None}  # d=+1: sell-side pool (swing low) for a long; [level, swept]
    pending = {1: None, -1: None}  # penetration waiting one bar for the close back
    active = {1: None, -1: None}  # confirmed sweep waiting for the shift
    for j in range(len(m5)):
        a = atr[j]
        for d in (1, -1):
            # G1 shift: close beyond the latest confirmed opposite swing within 6 bars of the sweep
            sw = active[d]
            if sw and j > sw["s"] + 6:
                active[d] = sw = None
                diag["no_shift"] += 1
            if sw and j >= sw["r"]:
                opp = pool[-d]
                if opp and (c[j] - opp[0]) * d > 0:
                    active[d] = None
                    s, t = sw["s"], m5.ctime.iat[j]
                    if session_of(t) is None:  # eligible: London and New York sessions only
                        diag["outside_sessions"] += 1
                        continue
                    if not (pin(o[s], h[s], l_[s], c[s], d, atr[s]) or pin(o[j], h[j], l_[j], c[j], d, a)):
                        diag["no_g4"] += 1
                        continue
                    hi_, lo_ = asof(ext_hi, "v", t), asof(ext_lo, "v", t)
                    eq = (hi_ + lo_) / 2
                    if np.isnan(eq) or (c[j] - eq) * d >= 0:  # long only below eq, short only above
                        diag["no_g3"] += 1
                        continue
                    if asof(h1, "trend", t) == -d:
                        diag["no_trade_regime"] += 1
                        continue
                    spr = m5.spr.iat[j]
                    slp = sw["ext"] - 0.1 * a - spr if d > 0 else sw["ext"] + 0.1 * a + spr
                    entry = c[j] + spr if d > 0 else c[j]
                    out.append(setup(m5, j, d, abs(entry - slp), session_of(t)))
                    diag["setups"] += 1
            # G2 sweep of the latest confirmed pool by >= 0.05 ATR, close back within 1 bar
            p = pending[d]
            if p:
                pending[d] = None
                if (c[j] - p["lvl"]) * d > 0:
                    ext = min(p["ext"], l_[j]) if d > 0 else max(p["ext"], h[j])
                    active[d] = {"s": p["s"], "r": j, "ext": ext}
                    diag["sweeps"] += 1
            pl = pool[d]
            if pl and not pl[1] and not np.isnan(a):
                pen = (pl[0] - l_[j]) if d > 0 else (h[j] - pl[0])
                if pen >= 0.05 * a:
                    pl[1] = True
                    ext = l_[j] if d > 0 else h[j]
                    if (c[j] - pl[0]) * d > 0:
                        active[d] = {"s": j, "r": j, "ext": ext}
                        diag["sweeps"] += 1
                    else:
                        pending[d] = {"s": j, "lvl": pl[0], "ext": ext}
        if j >= 2 and sl[j - 2]:
            pool[1] = [l_[j - 2], False]
        if j >= 2 and sh[j - 2]:
            pool[-1] = [h[j - 2], False]
    return out


# ---------------------------------------------------------------- evaluation
def evaluate(setups: list[dict], p01: str, max_hold: int, quota: int, by_session: bool) -> dict:
    budget, codes = budget_for(p01), Counter()
    accepted, open_until = Counter(), None
    for s in sorted(setups, key=lambda x: x["t"]):
        key = (s["day"], s["session"] if by_session else None)
        if accepted[key] >= quota:
            codes["suppressed_by_rule_quota"] += 1
            continue
        if not s["liquid"]:
            code = "OUTSIDE_STRATEGY_ENVELOPE"
        elif pre_close(s["t"], max_hold):
            code = "PRE_CLOSE"
        elif np.isnan(s["med20"]):
            code = "CALC_UNAVAILABLE"
        elif s["spr"] > min(2.0 * s["med20"], 0.10 * s["D"]):  # P-13 min(B, C)
            code = "SPREAD_TOO_WIDE"
        else:
            # shortcut: occupancy = full max_hold (SL/TP exits not simulated, RES-021); an upper bound
            busy = open_until is not None and s["t"] < open_until
            code, _ = risk_engine(budget, dec(s["D"]), dec(s["med20"]), dec(s["price"]), busy)
        codes[code or "SURVIVED"] += 1
        if code is None:
            accepted[key] += 1
            open_until = s["t"] + pd.Timedelta(minutes=max_hold)
    signals = sum(v for k, v in codes.items() if k != "suppressed_by_rule_quota")
    excluded = sum(codes[k] for k in EXCLUDED_CODES)
    denom = signals - excluded
    passed_gates = denom - codes["SPREAD_TOO_WIDE"]
    a10 = sum(codes[k] for k in A10_CODES)
    return dict(budget=str(budget), codes=dict(codes), signals=signals, excluded=excluded,
                a10_denominator=denom, a10_rate=a10 / denom if denom else None,
                passed_pretrade_gates=passed_gates,
                min_volume_rate=codes["MIN_VOLUME_EXCEEDS_BUDGET"] / passed_gates if passed_gates else None,
                survived=codes["SURVIVED"])


def walls(p01: str, slip: float, price: float, spread: float) -> dict:
    """Item 2 and the feasible-window walls at 10,000 USC (ILL-CENT)."""
    b = float(budget_for(p01))
    d_max = b / float(VOL_MIN * USC_PER_USD_LOT) - slip  # RISK-013 with P-26 at volume_min
    vol_lev = math.floor(float(EQUITY * P09) / (price * float(USC_PER_USD_LOT)) / 0.01 + 1e-9) * 0.01
    exp_floor = b / ((vol_lev + 0.01) * float(USC_PER_USD_LOT)) - slip  # stops <= this: EFFECTIVE_LEVERAGE
    return dict(d_max=d_max, exposure_floor=exp_floor, p09_max_volume=round(vol_lev, 2),
                spread_floor=spread / 0.10)


def classify(a10: float | None) -> str:
    """Pre-declared (before the run): < 40% FEASIBLE, 40-60% MARGINAL, > 60% INFEASIBLE (CENT-031 at 50%)."""
    if a10 is None:
        return "N/A"
    return "FEASIBLE" if a10 < 0.40 else "MARGINAL" if a10 <= 0.60 else "INFEASIBLE"


def wilson(k: int, n: int) -> tuple[float, float]:
    """95% Wilson interval for a rate k/n (sampling uncertainty of the A10 rate only)."""
    if n == 0:
        return (float("nan"), float("nan"))
    p, z = k / n, 1.96
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (c - h, c + h)


def pct(x) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.1f}%"


def tables(runs: dict) -> str:
    """Markdown tables for docs/research/feasibility_spike.md."""
    lines = [f"**{LABEL}** — stop distances and spreads per candidate (all signals, before any gate)", "",
             "| Candidate | Window (server time) | Weeks | Signals | Stop D median (USD) | D P10 | D P90 "
             "| Median bar spread (USD) | Median round-trip spread ÷ D | Median P-26 (USD) | Median entry price (USD) |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for n, r in runs.items():
        w = f"{r['window'][0][:10]} .. {r['window'][1][:10]}"
        lines.append(f"| {n} | {w} | {r['weeks']:.1f} | {r['setups']} | {r['D_median']:.2f} | {r['D_p10']:.2f} "
                     f"| {r['D_p90']:.2f} | {r['spread_median']:.3f} | {pct(r['spread_share_median'])} "
                     f"| {r['p26_median']:.3f} | {r['price_median']:.0f} |")
    lines += ["", f"**{LABEL}** — sizing feasibility at 10,000.00 USC, `ILL-CENT`, fixture parameters", "",
              "| Candidate | P-01 | Budget (USC) | Widest stop at min lot (USD) | Exposure floor: stops ≤ this rejected (USD) "
              "| Spread floor (USD) | Signals | Excluded (envelope / pre-close / calc) | A10 denominator "
              "| `MIN_VOLUME_EXCEEDS_BUDGET` rate (CENT-030) | A10 capital-feasibility rate [95% interval] "
              "| Survived | Survived per week | Class |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for n, r in runs.items():
        for p, v in r["levels"].items():
            c, w = v["codes"], v["walls"]
            exc = "/".join(str(c.get(k, 0)) for k in EXCLUDED_CODES)
            a10k = sum(c.get(k, 0) for k in A10_CODES)
            lo, hi = wilson(a10k, v["a10_denominator"])
            lines.append(f"| {n} | {p}% | {v['budget']} | {w['d_max']:.2f} | {w['exposure_floor']:.2f} "
                         f"| {w['spread_floor']:.2f} | {v['signals']} | {exc} | {v['a10_denominator']} "
                         f"| {pct(v['min_volume_rate'])} ({c.get('MIN_VOLUME_EXCEEDS_BUDGET', 0)}/{v['passed_pretrade_gates']}) "
                         f"| {pct(v['a10_rate'])} ({a10k}/{v['a10_denominator']}) [{pct(lo)}–{pct(hi)}] "
                         f"| {v['survived']} | {v['survived_per_week']:.2f} | {v['class']} |")
    lines += ["", f"**{LABEL}** — A10 rejections split by code (count; share of the A10 denominator)", "",
              "| Candidate | P-01 | " + " | ".join(f"`{k}`" for k in A10_CODES) + " | Suppressed by the rule's own trade quota |",
              "| --- | --- | " + " | ".join("---" for _ in A10_CODES) + " | --- |"]
    for n, r in runs.items():
        for p, v in r["levels"].items():
            c, dnm = v["codes"], v["a10_denominator"]
            cells = [f"{c.get(k, 0)} ({pct(c.get(k, 0) / dnm if dnm else None)})" for k in A10_CODES]
            lines.append(f"| {n} | {p}% | " + " | ".join(cells) + f" | {c.get('suppressed_by_rule_quota', 0)} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    _self_check()
    OUT.mkdir(exist_ok=True)
    m5_all = pd.read_parquet(DATA / "XAUUSDm_M5.parquet").sort_values("time").reset_index(drop=True)
    h1_all = pd.read_parquet(DATA / "XAUUSDm_H1.parquet").sort_values("time").reset_index(drop=True)
    cut_m5, cut_h1 = holdout_cut(m5_all.time), holdout_cut(h1_all.time)

    m5 = add_cost_context(prep(m5_all[m5_all.time < cut_m5], pd.Timedelta("5min")))
    m15 = prep(resample(m5, "15min"), pd.Timedelta("15min"))
    h1r = add_cost_context(prep(resample(m5, "1h"), pd.Timedelta("1h")))
    h4r = prep(resample(h1r, "4h"), pd.Timedelta("4h"))

    # B-hist: dense part of the H1 file (first month with >= 400 bars) up to the H1 cut
    h1c = h1_all[h1_all.time < cut_h1]
    per_month = h1c.groupby(h1c.time.dt.tz_localize(None).dt.to_period("M")).size()
    dense_start = per_month[per_month >= 400].index[0].start_time.tz_localize(UTC)
    h1 = add_cost_context(prep(h1c[h1c.time >= dense_start], pd.Timedelta("1h")))
    h4 = prep(resample(h1, "4h"), pd.Timedelta("4h"))

    runs = {}
    diags = {k: Counter() for k in ("A", "B-recent", "B-hist", "C")}
    specs = {
        "A": (candidate_a(m5, m15, h1r, diags["A"]), 240, 1, True, m5),
        "B-recent": (candidate_b(h1r, h4r, diags["B-recent"]), 360, 1, False, h1r),
        "B-hist": (candidate_b(h1, h4, diags["B-hist"]), 360, 1, False, h1),
        "C": (candidate_c(m5, m15, h1r, diags["C"]), 60, 3, True, m5),
    }
    for name, (setups, max_hold, quota, by_sess, src) in specs.items():
        D = np.array([s["D"] for s in setups])
        spr = np.array([s["spr"] for s in setups])
        med20 = np.nanmedian([s["med20"] for s in setups]) if setups else float("nan")
        price = float(np.median([s["price"] for s in setups])) if setups else float("nan")
        weeks = (src.time.iloc[-1] - src.time.iloc[0]).total_seconds() / (7 * 86400)
        levels = {}
        for p in P01_LEVELS:
            ev = evaluate(setups, p, max_hold, quota, by_sess)
            ev["survived_per_week"] = ev["survived"] / weeks
            ev["class"] = classify(ev["a10_rate"])
            ev["walls"] = walls(p, med20, price, float(np.median(spr)))
            levels[p] = ev
        runs[name] = dict(
            label=LABEL, window=[str(src.time.iloc[0]), str(src.time.iloc[-1])], weeks=weeks,
            setups=len(setups), diag=dict(diags[name]),
            D_median=float(np.median(D)), D_p10=float(np.percentile(D, 10)),
            D_p90=float(np.percentile(D, 90)),
            spread_median=float(np.median(spr)), spread_share_median=float(np.median(spr / D)),
            p26_median=float(med20), price_median=price, levels=levels)
    meta = dict(label=LABEL, cut_m5=str(cut_m5), cut_h1=str(cut_h1), h1_dense_start=str(dense_start),
                m5_first=str(m5_all.time.iloc[0]), m5_last=str(m5_all.time.iloc[-1]),
                h1_first=str(h1_all.time.iloc[0]), h1_last=str(h1_all.time.iloc[-1]))
    (OUT / "results.json").write_text(json.dumps(dict(meta=meta, runs=runs), indent=2, default=str),
                                      encoding="utf-8", newline="\n")
    (OUT / "tables.md").write_text(tables(runs), encoding="utf-8", newline="\n")
    print(json.dumps(meta, indent=2))
    for name, r in runs.items():
        print(name, r["setups"], r["diag"])


if __name__ == "__main__":
    main()
