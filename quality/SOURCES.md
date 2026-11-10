# SOURCES — External references used by the V2 pack

All access dates are **2026-11-08**. The **Status** column shows how far each source was
checked in this session:

- **FETCHED**: the page was retrieved and its content read in this session.
- **SEARCH-ONLY**: the page was found by search, but its content was not retrieved.
- **PRIOR-RESEARCH**: the source was retrieved during the V1 research task in the same
  conversation and was not re-retrieved for V2.
- **UNREACHABLE**: the page could not be retrieved in this session (site error). Any claim
  that rests only on it is marked `REPORTED` and must be checked against the live account
  in M2.

Specification files cite sources as `[S#]`.

| ID | Source | URL | Status | Used for |
|---|---|---|---|---|
| S1 | Exness Help Centre: "Are demo accounts available for all account types?" | https://get.exness.help/hc/en-us/articles/360010683800-Are-demo-accounts-available-for-all-account-types | FETCHED | Standard Cent has no demo account |
| S2 | Exness: Commodities trading page | https://www.exness.com/commodities/ | FETCHED | Gold hours (XAU, server time GMT+0: Sun 22:05 – Fri 20:58, daily break 20:58–22:01); Wednesday triple swap; leverage on new gold positions capped at 1:200 during news releases; floating spreads |
| S3 | Exness Help Centre: "About swap" | https://get.exness.help/hc/en-us/articles/360014709151-About-swap | FETCHED | Swap applied at 21:00 GMT+0 (summer) / 22:00 GMT+0 (winter); triple swap on Wednesdays for metals; automatic swap-free status for accounts registered in Islamic countries |
| S4 | Exness Help Centre: "Standard Cent account" | https://get.exness.help/hc/en-us/articles/17537782786588-Standard-Cent-account | UNREACHABLE in both V2 sessions (V1 research reported its content) | REPORTED: USC currency; 1 cent lot = 0.01 standard lot; high/"unlimited" leverage options; low stop-out level |
| S5 | Exness Help Centre: "Higher Margin Requirements (HMR)" | https://get.exness.help/hc/en-us/articles/20618327917596-Higher-Margin-Requirements-HMR | UNREACHABLE (V1 research reported its content) | REPORTED: higher margin around high-impact news and before market breaks |
| S6 | MQL5 Reference: `TimeCurrent()` | https://www.mql5.com/en/docs/dateandtime/timecurrent | FETCHED | Last known server time = time of the last quote received; formed on the server |
| S7 | MQL5 Reference: `TimeTradeServer()` | https://www.mql5.com/en/docs/dateandtime/timetradeserver | FETCHED | Calculated current server time; computed in the client terminal, so it depends on the local clock |
| S8 | MQL5 Reference: `TimeGMT()` | https://www.mql5.com/en/docs/dateandtime/timegmt | FETCHED | Derived from the local computer time with local DST; equals simulated server time in the tester |
| S9 | MQL5 Reference: Python Integration (function list) | https://www.mql5.com/en/docs/python_metatrader5 | FETCHED | Available Python functions; there is **no** Python equivalent of `TimeTradeServer` |
| S10 | MQL5 Reference: Python `copy_ticks_range` | https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py | FETCHED | Docs say tick/bar times are stored "in UTC time zone (without the shift)"; tick fields include time, time_msc, bid, ask, last, volume, flags |
| S11 | MQL5 Reference: Python `order_calc_profit` | https://www.mql5.com/en/docs/python_metatrader5/mt5ordercalcprofit_py | FETCHED | Returns profit in account currency, or `None` on failure |
| S12 | MQL5 Reference: Python `order_calc_margin` | https://www.mql5.com/en/docs/python_metatrader5/mt5ordercalcmargin_py | FETCHED | Returns margin in account currency; **ignores existing orders and positions** |
| S13 | MQL5 Reference: Symbol properties | https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants | FETCHED | Definitions of stops level, freeze level, tick size/value, volume min/max/step, triple-swap day, filling mode, contract size, profit currency |
| S14 | MQL5 Reference: Trade server return codes | https://www.mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes | FETCHED | Retcodes 10004–10046 |
| S15 | MQL5 Reference: Client terminal properties | https://www.mql5.com/en/docs/constants/environment_state/terminalstatus | FETCHED | `TERMINAL_CONNECTED`, `TERMINAL_TRADE_ALLOWED`, `TERMINAL_COMMONDATA_PATH`, `TERMINAL_PING_LAST` |
| S16 | MQL5 Reference: `FileMove` | https://www.mql5.com/en/docs/files/filemove | FETCHED | `FILE_REWRITE` and `FILE_COMMON` flags for replace-by-rename |
| S17 | MQL5 Book: cryptographic methods overview | https://www.mql5.com/en/book/advanced/crypt/crypt_overview | FETCHED | `CRYPT_HASH_SHA256` exists; no native HMAC (it must be built from SHA-256) |
| S18 | PyPI: MetaTrader5 package | https://pypi.org/project/metatrader5 | FETCHED | v5.0.6231 (released 2026-09-27); Windows x86-64 wheels only; CPython 3.6–3.14 |
| S19 | Python docs: `decimal` | https://docs.python.org/3/library/decimal.html | FETCHED | `Decimal(float)` converts exactly, e.g. `Decimal(1.1)` = 1.1000000000000000888…; `FloatOperation` trap; `quantize`; rounding modes |
| S20 | MCP specification: Authorization (2025-06-18) | https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization | FETCHED | STDIO servers should not use the OAuth flow and should take credentials from the environment; audience-bound tokens; no token passthrough |
| S21 | MCP docs: Security Best Practices (2026-07-28) | https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices | FETCHED | Local server compromise, prefer stdio for local servers, scope minimisation, token passthrough, SSRF, state-handle hijacking |
| S22 | MCP blog: "The 2026-07-28 Specification" | https://blog.modelcontextprotocol.io/posts/2026-07-28/ | FETCHED | Current spec version; stateless protocol; HTTP+SSE deprecated; DCR deprecated in favour of CIMD |
| S23 | MCP specification: Transports | https://modelcontextprotocol.io/specification/2025-03-26/basic/transports | SEARCH-ONLY | stdio and Streamable HTTP transports |
| S24 | OWASP GenAI: LLM01:2025 Prompt Injection | https://genai.owasp.org/llmrisk/llm01-prompt-injection/ | SEARCH-ONLY | Prompt injection, including indirect injection |
| S25 | OWASP GenAI: LLM02:2025 Sensitive Information Disclosure | https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/ | SEARCH-ONLY | Leakage of sensitive data through LLMs |
| S26 | W3C: WCAG 2.2 | https://www.w3.org/TR/WCAG22/ | SEARCH-ONLY | SC 1.4.3 contrast, 1.4.11 non-text contrast, 2.4.7 focus visible, 2.4.13 focus appearance |
| S27 | Bailey, D. & López de Prado, M. (2014). The Deflated Sharpe Ratio. *Journal of Portfolio Management* 40(5) | (journal article) | PRIOR-RESEARCH | DSR |
| S28 | Bailey, Borwein, López de Prado & Zhu (2017). The Probability of Backtest Overfitting. *Journal of Computational Finance* 20(4) | https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf | PRIOR-RESEARCH | PBO via CSCV |
| S29 | López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley | (book) | NOT RETRIEVED; standard reference | Purging and embargo for overlapping labels |
| S30 | Chen et al. (2025). StockBench, arXiv:2510.02209 | https://arxiv.org/abs/2510.02209 | PRIOR-RESEARCH | Weak/inconsistent live LLM trading results |
| S31 | AI-Trader (2025), arXiv:2512.10971 | https://arxiv.org/html/2512.10971v1 | PRIOR-RESEARCH | Weak live LLM trading results |
| S32 | HackerNoon: SuperTrend backtest on Exness tick archives (2026) | https://hackernoon.com/the-truth-about-tradingviews-supertrend-strategy-after-67-years-of-backtesting | PRIOR-RESEARCH (secondary, single strategy) | Thin edge erased by cent-account costs |
| S33 | Exness Help Centre: Instrument trading hours | https://get.exness.help/hc/en-us/articles/4405235684498-Instrument-trading-hours | SEARCH-ONLY | Session calendar (to be read live in M2) |
| S34 | MQL5 Reference: `OnTradeTransaction` | https://www.mql5.com/en/docs/event_handlers/ontradetransaction | SEARCH-ONLY | Guardian event-driven trade monitoring |
| S35 | MQL5 Reference: `MqlTradeRequest` structure | https://www.mql5.com/en/docs/constants/structures/mqltraderequest | FETCHED | Fields: action, magic (Expert Advisor ID), order, symbol, volume, price, stoplimit, sl, tp, deviation, type, type_filling, type_time, expiration, comment, position, position_by. **No client idempotency or request-ID field** |
| S36 | MQL5 Reference: `SymbolInfoSessionTrade` | https://www.mql5.com/en/docs/marketinformation/symbolinfosessiontrade | FETCHED | Sessions per **weekday** and session index only; no calendar dates, holidays or exceptions |
| S37 | MQL5 Reference: Deal properties | https://www.mql5.com/en/docs/constants/tradingconstants/dealproperties | FETCHED | `DEAL_TYPE_BALANCE`, `CREDIT`, `CHARGE`, `CORRECTION`, `BONUS`, commission types; `DEAL_COMMISSION`, `DEAL_FEE`, `DEAL_SWAP` |
| S38 | MQL5 Reference: `OrderCalcProfit` | https://www.mql5.com/en/docs/trading/ordercalcprofit | FETCHED | Returns profit in account currency; returns false on failure; only BUY/SELL types; an estimate under current conditions |
| S39 | MQL5 Reference: Python `order_send` | https://www.mql5.com/en/docs/python_metatrader5/mt5ordersend_py | SEARCH-ONLY | Python trade request sending |

## Rules for using these sources

1. Broker facts (S2–S5, S33) can change without notice. **Live `symbol_info()`,
   `account_info()` and `terminal_info()` values from the connected account always override a
   document** (CENT-001).
2. S4 and S5 were unreachable in this session. Every claim that depends only on them is
   `REPORTED` until M2 confirms it from the live account.
3. Where S10 ("UTC without the shift") conflicts with widely reported practice (epoch values
   that represent broker wall-clock time), V2 does not assume either reading. M2 measures it
   (TIME-005).
