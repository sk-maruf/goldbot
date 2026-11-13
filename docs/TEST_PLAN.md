# TEST_PLAN — GoldBot

> **GENERATED FILE — do not edit by hand.** Produced by `tools/gen_test_plan.py` from
> `quality/REQUIREMENTS_TRACEABILITY.md` (columns ID, Requirement, Component, Verification,
> Acceptance criterion, Crit.) and `specifications/GUARDIAN_SAFETY_SPEC.md` §13. Change the
> sources, then run `python tools/gen_test_plan.py`. `--check` exits 1 when this file is
> stale.
>
> This is a plan. It holds no test results and moves no requirement to `VERIFIED`
> (GOV-002).
>
> Process/review-only rows (every part of `Verification` is a review, STATUS audit,
> evidence table, inspection, manual, document, CI or `[HUMAN]` marker; §2) get the test
> `REVIEW (no automated test)` or `HUMAN step` instead of a pytest path, and are verified by the
> 02 review or by the human step with its evidence (`docs/DEFINITION_OF_DONE.md`).

## 1. Coverage targets

| Scope | Target | Source |
| --- | --- | --- |
| `src/goldbot/core/` (whole package) | >= 95% branch | kickoff §5 (TEST_PLAN row) |
| `core/risk_engine.py`, `core/sizing.py` | 100% branch | kickoff §5; 01 prompt M3 |
| `core/exposure.py`, `core/trading_state.py` | 100% branch | 01 prompt M3 |
| `core/money.py`, `core/convert.py` | >= 95% branch | 01 prompt M1 |
| `src/goldbot/intelligence/` | >= 95% branch | 01 prompt M6a/M6b, M6c/M6d |
| Whole Python codebase | >= 80% | kickoff §5 (TEST_PLAN row) |
| `sizing.py` rounding and rejection branches | mutation spot check, no surviving mutants | 01 prompt M3 |

## 2. Mapping and naming rules

- **Test type** = the requirement's `Verification` cell, verbatim. Empty → `UNMAPPED`.
- **Milestones** = every `M<n>[part]` token after `passes in` in the `Acceptance
  criterion` cell; a range `Mx–My` includes every milestone between. A requirement is
  listed under each milestone it names. `02 review checks it each milestone` → `EACH`.
  Nothing found → `UNMAPPED`.
- **Area** = the `tests/` folder of the M1 layout: the first rule below whose keyword
  occurs
  in the first `+`-separated part of the test type (the primary test); otherwise
  `unit`.
  Rules in order: `playwright` → e2e, `e2e` → e2e, `security` → security, `privacy` → security, `route` → security, `chaos` → chaos, `mql5` → integration, `fakebroker` → integration, `integration` → integration, `live` → integration, `demo` → integration, `replay` → integration, `golden` → golden, `property` → property, `truncation` → property.
- **Test name** = `tests/<area>/test_<id>_<slug>.py::test_<id>_<slug>`, where `<id>` is the
  requirement ID lower-cased with `-` → `_`, and `<slug>` is the first four lower-case
  alphanumeric words of the requirement summary joined by `_`, cut to 40 characters. The
  function name starts with the `test_<id>` named in the traceability acceptance
  criterion. A requirement checked by review also gets this test for its automatable part
  (scan, audit); the review itself is in `docs/DEFINITION_OF_DONE.md`.
- **Process/review-only** = every `+`-separated part of the test type matches one of these
  case-insensitive regex markers: `\breview\b`, `\bstatus audit\b`, `\bevidence table\b`, `\binspection\b`, `\bmanual\b`, `\bdocument\b`, `\bci\b`, `\[human\]`. Such a row gets the test
  `REVIEW (no automated test)` (or `HUMAN step` when the test type contains `[HUMAN]`), never a
  pytest path, because a pytest for a process rule could only be tautological. It is verified
  by the 02 review (or by the human step and its evidence). A test type with one automated
  part keeps the pytest name.
- **mt5** = `yes` when the test type mentions `live`, `demo`, `mql5`: at least part of the
  test needs the Windows host with the terminal (`pytest -m mt5`).

## 3. Totals

Requirements: **442** unique IDs.

### 3.1 Per milestone

A requirement that names several milestones counts once in each.

| Milestone | Requirements | CRITICAL |
| --- | --- | --- |
| M0b | 1 | 1 |
| M1 | 51 | 43 |
| M2 | 75 | 75 |
| M3 | 74 | 74 |
| M4 | 49 | 18 |
| M5 | 25 | 4 |
| M6 | 28 | 10 |
| M6a | 14 | 7 |
| M6b | 15 | 8 |
| M6c | 13 | 5 |
| M6d | 23 | 14 |
| M6e | 17 | 8 |
| M6f | 2 | 1 |
| M7 | 68 | 68 |
| M8 | 87 | 66 |
| M9 | 49 | 19 |
| EACH | 10 | 5 |

### 3.2 Per test type

| Test type | Requirements |
| --- | --- |
| Unit + property + golden vectors | 41 |
| FakeBroker integration + demo chaos | 36 |
| MQL5 test script + demo scenarios | 31 |
| Reference-value tests + registry audit | 28 |
| Micro-scenario + determinism tests | 25 |
| MCP security tests | 23 |
| Unit (injected clocks) + M2 live measurement | 23 |
| Playwright + axe + visual snapshots | 22 |
| Live discovery checks + golden vectors | 21 |
| Privacy tests + inspection | 21 |
| Route × scope matrix + security tests | 19 |
| Security tests + review | 18 |
| Unit tests | 12 |
| Schema/migration tests | 10 |
| Unit + golden vectors (VER profiles) | 9 |
| Health-state unit tests + M9 targets | 8 |
| Review (02 prompt) + STATUS audit | 6 |
| Static import test + payload tests | 6 |
| Playwright + axe + UNKNOWN-state tests | 2 |
| Property test (future truncation) | 2 |
| Registry trial-count test | 2 |
| Schema + unit tests | 2 |
| Unit + future-truncation tests | 2 |
| Unit tests on hand-labelled synthetic bars | 2 |
| Wording scan + review | 2 |
| 03 prompt evidence table | 1 |
| Backtest report test | 1 |
| Breakdown-sum unit test | 1 |
| CENT tests (existing) | 1 |
| Config schema test + review | 1 |
| Count-once property test | 1 |
| Count-once unit test | 1 |
| Determinism test | 1 |
| Docs check + versioning test | 1 |
| E2E (Playwright) + privacy check | 1 |
| FakeBroker + demo integration tests | 1 |
| Fault-injection test | 1 |
| Field-completeness test | 1 |
| Group-mapping unit test | 1 |
| Hand-labelled fixtures per table row | 1 |
| Integration test | 1 |
| Integration test (backtester + engine path) | 1 |
| Integration test (each requirement blocks) | 1 |
| Migration up/down test + decision-record equality | 1 |
| Ownership + unit tests | 1 |
| Ownership test + unit tests | 1 |
| Playwright + wording scan | 1 |
| Property test (closed higher-timeframe bars) | 1 |
| Property test (never widens) | 1 |
| Property test (no skipped state) + static test | 1 |
| REPLAY field-completeness test | 1 |
| Reference-value tests against RES-030 | 1 |
| Reference-value unit tests | 1 |
| Registry audit | 1 |
| Registry audit + report check | 1 |
| Registry audit + selector-input test | 1 |
| Registry test (V2.1 versions unchanged) | 1 |
| Report test | 1 |
| Report test (never a live input) | 1 |
| Report test + holdout-touch audit | 1 |
| Research report (MI-196) | 1 |
| Review (02 check 47) + config audit | 1 |
| Review (02 prompt) + CI | 1 |
| Review + golden vectors | 1 |
| STATUS audit | 1 |
| Schema + persistence tests | 1 |
| Selector pre-registration audit | 1 |
| Static + integration tests (evaluate_* only) | 1 |
| Static import test | 1 |
| Static import test + purity tests | 1 |
| Static input test | 1 |
| Static test + property test (confidence never reaches sizing) | 1 |
| Unit + backtest tests | 1 |
| Unit + closed-bar property tests | 1 |
| Unit + envelope tests | 1 |
| Unit + golden vector (GV-41) | 1 |
| Unit + golden vectors (GV-33, GV-39, GV-40) | 1 |
| Unit + property tests | 1 |
| Unit test (FORMING never supports a candidate) | 1 |
| Unit test (RISK-016) | 1 |
| Unit test (fixed priority, no selection) | 1 |
| Unit test (minimum volume) | 1 |
| Unit test (one candle never exits) | 1 |
| Unit tests (P-27, RISK-032/034) | 1 |
| Unit tests (backtest only) | 1 |
| Unit tests (bar building, sessions, timestamps) | 1 |
| Unit tests (boundaries) | 1 |
| Unit tests (costs, closed bar) | 1 |
| Unit tests (gates only block) | 1 |
| Unit tests (sweep vs wick) | 1 |
| Unit tests + research report | 1 |
| Unit tests + wording scan | 1 |
| Unit tests per method | 1 |
| Unit tests with injected data faults | 1 |

### 3.3 Per area

| Area | Requirements | of which mt5 |
| --- | --- | --- |
| `tests/e2e/` | 26 | 0 |
| `tests/integration/` | 94 | 90 |
| `tests/property/` | 6 | 0 |
| `tests/security/` | 81 | 0 |
| `tests/unit/` | 226 | 23 |
| REVIEW (no automated test) | 9 | |

## 4. Requirements by milestone

### M0b (1)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| MI-061 | CRITICAL | Config schema test + review | M0b/M3 |  | `tests/unit/test_mi_061_risk_profiles_a_risk.py::test_mi_061_risk_profiles_a_risk` |

### M1 (51)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| DATA-001 | HIGH | Schema/migration tests | M1 |  | `tests/unit/test_data_001_single_writer_per_table.py::test_data_001_single_writer_per_table` |
| DATA-002 | HIGH | Schema/migration tests | M1 |  | `tests/unit/test_data_002_ids_uuidv7_for_every.py::test_data_002_ids_uuidv7_for_every` |
| DATA-003 | HIGH | Schema/migration tests | M1 |  | `tests/unit/test_data_003_timestamps_utc_timezone_aware.py::test_data_003_timestamps_utc_timezone_aware` |
| DATA-004 | CRITICAL | Schema/migration tests | M1 |  | `tests/unit/test_data_004_money_columns_are_stored.py::test_data_004_money_columns_are_stored` |
| DATA-005 | CRITICAL | Schema/migration tests | M1 |  | `tests/unit/test_data_005_env_tagging_every_row.py::test_data_005_env_tagging_every_row` |
| DATA-010 | HIGH | Schema/migration tests | M1 |  | `tests/unit/test_data_010_every_schema_has_schema.py::test_data_010_every_schema_has_schema` |
| DATA-011 | HIGH | Schema/migration tests | M1 |  | `tests/unit/test_data_011_a_ci_test_keeps.py::test_data_011_a_ci_test_keeps` |
| DATA-020 | HIGH | Schema/migration tests | M1 |  | `tests/unit/test_data_020_migrations_are_versioned_scripts.py::test_data_020_migrations_are_versioned_scripts` |
| DATA-021 | HIGH | Schema/migration tests | M1 |  | `tests/unit/test_data_021_backups_and_restore_tests.py::test_data_021_backups_and_restore_tests` |
| DATA-022 | HIGH | Schema/migration tests | M1 |  | `tests/unit/test_data_022_pragma_integrity_check_daily.py::test_data_022_pragma_integrity_check_daily` |
| SEC-001 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_001_secrets_live_in_the.py::test_sec_001_secrets_live_in_the` |
| SEC-002 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_002_the_investor_password_is.py::test_sec_002_the_investor_password_is` |
| SEC-003 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_003_goldbot_never_asks_for.py::test_sec_003_goldbot_never_asks_for` |
| SEC-004 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_004_redaction_a_logging_filter.py::test_sec_004_redaction_a_logging_filter` |
| SEC-005 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_005_pre_commit_gitleaks_a.py::test_sec_005_pre_commit_gitleaks_a` |
| SEC-006 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_006_separate_permissions_monitoring_investor.py::test_sec_006_separate_permissions_monitoring_investor` |
| SEC-007 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_007_credential_compromise_response_t24.py::test_sec_007_credential_compromise_response_t24` |
| SEC-010 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_010_host_dedicated_windows_user.py::test_sec_010_host_dedicated_windows_user` |
| SEC-011 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_011_network_the_api_binds.py::test_sec_011_network_the_api_binds` |
| SEC-012 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_012_dependencies_uv_lock_pnpm.py::test_sec_012_dependencies_uv_lock_pnpm` |
| SEC-013 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_013_builds_ci_runs_lint.py::test_sec_013_builds_ci_runs_lint` |
| SEC-020 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_020_risk_limits_yaml_hash.py::test_sec_020_risk_limits_yaml_hash` |
| SEC-021 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_021_approval_tokens_hmac_over.py::test_sec_021_approval_tokens_hmac_over` |
| SEC-022 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_022_audit_log_append_only.py::test_sec_022_audit_log_append_only` |
| SEC-023 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_023_commands_approve_mode_change.py::test_sec_023_commands_approve_mode_change` |
| SEC-030 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_030_llm_inputs_are_built.py::test_sec_030_llm_inputs_are_built` |
| SEC-031 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_031_llm_outputs_are_parsed.py::test_sec_031_llm_outputs_are_parsed` |
| SEC-032 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_032_calendar_news_data_is.py::test_sec_032_calendar_news_data_is` |
| TIME-001 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_001_the_engine_never_calls.py::test_time_001_the_engine_never_calls` |
| TIME-005 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_005_tick_timestamp_interpretation_v2.py::test_time_005_tick_timestamp_interpretation_v2` |
| TIME-010 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_010_the_os_time_service.py::test_time_010_the_os_time_service` |
| TIME-011 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_011_all_persisted_timestamps_are.py::test_time_011_all_persisted_timestamps_are` |
| TIME-015 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_015_every_duration_p_15.py::test_time_015_every_duration_p_15` |
| TIME-020 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_020_the_adapter_polls_symbol.py::test_time_020_the_adapter_polls_symbol` |
| TIME-021 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_021_time_msc_must_be.py::test_time_021_time_msc_must_be` |
| TIME-022 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_022_quiet_market_vs_dead.py::test_time_022_quiet_market_vs_dead` |
| TIME-023 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_023_the_guardian_measures_freshness.py::test_time_023_the_guardian_measures_freshness` |
| TIME-030 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_030_on_every_guardian_heartbeat.py::test_time_030_on_every_guardian_heartbeat` |
| TIME-031 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_031_the_expected_offset_for.py::test_time_031_the_expected_offset_for` |
| TIME-032 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_032_both_timetradeserver_and_timegmt.py::test_time_032_both_timetradeserver_and_timegmt` |
| TIME-040 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_040_trading_sessions_come_from.py::test_time_040_trading_sessions_come_from` |
| TIME-041 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_041_swap_time_moves_between.py::test_time_041_swap_time_moves_between` |
| TIME-042 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_042_high_impact_usd_events.py::test_time_042_high_impact_usd_events` |
| TIME-043 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_043_calendar_validity_an_event.py::test_time_043_calendar_validity_an_event` |
| TIME-050 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_050_local_vs_ntp_offset.py::test_time_050_local_vs_ntp_offset` |
| TIME-051 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_051_server_offset_estimate_changes.py::test_time_051_server_offset_estimate_changes` |
| TIME-052 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_052_tick_timestamps_drift_from.py::test_time_052_tick_timestamps_drift_from` |
| TIME-053 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_053_guardian_heartbeat_clock_fields.py::test_time_053_guardian_heartbeat_clock_fields` |
| TIME-054 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_054_deal_order_timestamps_from.py::test_time_054_deal_order_timestamps_from` |
| TIME-055 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_055_missing_time_msc_on.py::test_time_055_missing_time_msc_on` |
| TIME-056 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_056_day_week_boundary_crossed.py::test_time_056_day_week_boundary_crossed` |

### M2 (75)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| CENT-001 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_001_live_values_win_values.py::test_cent_001_live_values_win_values` |
| CENT-002 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_002_account_discovery_record_account.py::test_cent_002_account_discovery_record_account` |
| CENT-003 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_003_symbol_discovery_symbols_get.py::test_cent_003_symbol_discovery_symbols_get` |
| CENT-004 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_004_spec_snapshot_fields_definitions.py::test_cent_004_spec_snapshot_fields_definitions` |
| CENT-005 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_005_sessions_the_python_package.py::test_cent_005_sessions_the_python_package` |
| CENT-006 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_006_commission_no_symbol_info.py::test_cent_006_commission_no_symbol_info` |
| CENT-007 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_007_swap_record_swap_mode.py::test_cent_007_swap_record_swap_mode` |
| CENT-010 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_010_profit_calc_order_calc.py::test_cent_010_profit_calc_order_calc` |
| CENT-011 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_011_currency_consistency_unit_of.py::test_cent_011_currency_consistency_unit_of` |
| CENT-012 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_012_scale_plausibility_under_cent.py::test_cent_012_scale_plausibility_under_cent` |
| CENT-013 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_013_margin_calc_order_calc.py::test_cent_013_margin_calc_order_calc` |
| CENT-014 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_014_volume_grid_volume_min.py::test_cent_014_volume_grid_volume_min` |
| CENT-015 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_015_stops_freeze_recorded_converted.py::test_cent_015_stops_freeze_recorded_converted` |
| CENT-016 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_016_account_type_evidence_no.py::test_cent_016_account_type_evidence_no` |
| CENT-017 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_017_tick_sanity_200_consecutive.py::test_cent_017_tick_sanity_200_consecutive` |
| CENT-018 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_018_repeatability_checks_re_run.py::test_cent_018_repeatability_checks_re_run` |
| CENT-020 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_020_re_validation_after_a.py::test_cent_020_re_validation_after_a` |
| CENT-030 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_030_for_each_strategy_and.py::test_cent_030_for_each_strategy_and` |
| CENT-031 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_031_if_the_rate_exceeds.py::test_cent_031_if_the_rate_exceeds` |
| CENT-032 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_032_cgv_06_shows_that.py::test_cent_032_cgv_06_shows_that` |
| CENT-040 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_040_the_m10_pilot_is.py::test_cent_040_the_m10_pilot_is` |
| GRD-001 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_001_the_guardian_is_an.py::test_grd_001_the_guardian_is_an` |
| GRD-002 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_002_hard_limits_come_from.py::test_grd_002_hard_limits_come_from` |
| GRD-003 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_003_the_engine_s_guardian.py::test_grd_003_the_engine_s_guardian` |
| GRD-004 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_004_the_guardian_never_opens.py::test_grd_004_the_guardian_never_opens` |
| GRD-005 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_005_size_target_1_000.py::test_grd_005_size_target_1_000` |
| GRD-006 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_006_atomic_write_the_writer.py::test_grd_006_atomic_write_the_writer` |
| GRD-007 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_007_reader_rules_open_with.py::test_grd_007_reader_rules_open_with` |
| GRD-008 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_008_channel_integrity_without_a.py::test_grd_008_channel_integrity_without_a` |
| GRD-010 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_010_the_engine_writes_engine.py::test_grd_010_the_engine_writes_engine` |
| GRD-011 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_011_the_guardian_writes_guardian.py::test_grd_011_the_guardian_writes_guardian` |
| GRD-012 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_012_staleness_the_guardian_considers.py::test_grd_012_staleness_the_guardian_considers` |
| GRD-013 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_013_if_the_engine_s.py::test_grd_013_if_the_engine_s` |
| GRD-015 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_015_when_the_engine_is.py::test_grd_015_when_the_engine_is` |
| GRD-016 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_016_clearing_the_guardian_s.py::test_grd_016_clearing_the_guardian_s` |
| GRD-018 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_018_positions_with_magic_magic.py::test_grd_018_positions_with_magic_magic` |
| GRD-019 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_019_every_guardian_trade_request.py::test_grd_019_every_guardian_trade_request` |
| GRD-020 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_020_missing_stop_response_within.py::test_grd_020_missing_stop_response_within` |
| GRD-021 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_021_the_guardian_never_moves.py::test_grd_021_the_guardian_never_moves` |
| GRD-025 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_025_the_guardian_keeps_its.py::test_grd_025_the_guardian_keeps_its` |
| GRD-026 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_026_when_equity_loss_its.py::test_grd_026_when_equity_loss_its` |
| GRD-027 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_027_on_restart_oninit_load.py::test_grd_027_on_restart_oninit_load` |
| GRD-028 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_028_session_end_backstop_if.py::test_grd_028_session_end_backstop_if` |
| GRD-030 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_030_all_documentation_and_ui.py::test_grd_030_all_documentation_and_ui` |
| GRD-031 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_031_guardian_failure_detection_by.py::test_grd_031_guardian_failure_detection_by` |
| GRD-032 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_032_audit_every_guardian_decision.py::test_grd_032_audit_every_guardian_decision` |
| GRD-033 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_033_terminal_disconnected_terminal_connected.py::test_grd_033_terminal_disconnected_terminal_connected` |
| GRD-040 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_040_takeover_reporting_any_guardian.py::test_grd_040_takeover_reporting_any_guardian` |
| GRD-041 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_041_sessions_calendar_weekly_export.py::test_grd_041_sessions_calendar_weekly_export` |
| GRD-050 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_050_lease_when_the_engine.py::test_grd_050_lease_when_the_engine` |
| GRD-051 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_051_check_then_act_before.py::test_grd_051_check_then_act_before` |
| GRD-052 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_052_sl_placement_by_the.py::test_grd_052_sl_placement_by_the` |
| TIME-001 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_001_the_engine_never_calls.py::test_time_001_the_engine_never_calls` |
| TIME-005 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_005_tick_timestamp_interpretation_v2.py::test_time_005_tick_timestamp_interpretation_v2` |
| TIME-010 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_010_the_os_time_service.py::test_time_010_the_os_time_service` |
| TIME-011 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_011_all_persisted_timestamps_are.py::test_time_011_all_persisted_timestamps_are` |
| TIME-015 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_015_every_duration_p_15.py::test_time_015_every_duration_p_15` |
| TIME-020 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_020_the_adapter_polls_symbol.py::test_time_020_the_adapter_polls_symbol` |
| TIME-021 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_021_time_msc_must_be.py::test_time_021_time_msc_must_be` |
| TIME-022 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_022_quiet_market_vs_dead.py::test_time_022_quiet_market_vs_dead` |
| TIME-023 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_023_the_guardian_measures_freshness.py::test_time_023_the_guardian_measures_freshness` |
| TIME-030 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_030_on_every_guardian_heartbeat.py::test_time_030_on_every_guardian_heartbeat` |
| TIME-031 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_031_the_expected_offset_for.py::test_time_031_the_expected_offset_for` |
| TIME-032 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_032_both_timetradeserver_and_timegmt.py::test_time_032_both_timetradeserver_and_timegmt` |
| TIME-040 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_040_trading_sessions_come_from.py::test_time_040_trading_sessions_come_from` |
| TIME-041 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_041_swap_time_moves_between.py::test_time_041_swap_time_moves_between` |
| TIME-042 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_042_high_impact_usd_events.py::test_time_042_high_impact_usd_events` |
| TIME-043 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_043_calendar_validity_an_event.py::test_time_043_calendar_validity_an_event` |
| TIME-050 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_050_local_vs_ntp_offset.py::test_time_050_local_vs_ntp_offset` |
| TIME-051 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_051_server_offset_estimate_changes.py::test_time_051_server_offset_estimate_changes` |
| TIME-052 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_052_tick_timestamps_drift_from.py::test_time_052_tick_timestamps_drift_from` |
| TIME-053 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_053_guardian_heartbeat_clock_fields.py::test_time_053_guardian_heartbeat_clock_fields` |
| TIME-054 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_054_deal_order_timestamps_from.py::test_time_054_deal_order_timestamps_from` |
| TIME-055 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_055_missing_time_msc_on.py::test_time_055_missing_time_msc_on` |
| TIME-056 | CRITICAL | Unit (injected clocks) + M2 live measurement | M1–M2 | yes | `tests/unit/test_time_056_day_week_boundary_crossed.py::test_time_056_day_week_boundary_crossed` |

### M3 (74)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| CENT-001 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_001_live_values_win_values.py::test_cent_001_live_values_win_values` |
| CENT-002 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_002_account_discovery_record_account.py::test_cent_002_account_discovery_record_account` |
| CENT-003 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_003_symbol_discovery_symbols_get.py::test_cent_003_symbol_discovery_symbols_get` |
| CENT-004 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_004_spec_snapshot_fields_definitions.py::test_cent_004_spec_snapshot_fields_definitions` |
| CENT-005 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_005_sessions_the_python_package.py::test_cent_005_sessions_the_python_package` |
| CENT-006 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_006_commission_no_symbol_info.py::test_cent_006_commission_no_symbol_info` |
| CENT-007 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_007_swap_record_swap_mode.py::test_cent_007_swap_record_swap_mode` |
| CENT-010 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_010_profit_calc_order_calc.py::test_cent_010_profit_calc_order_calc` |
| CENT-011 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_011_currency_consistency_unit_of.py::test_cent_011_currency_consistency_unit_of` |
| CENT-012 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_012_scale_plausibility_under_cent.py::test_cent_012_scale_plausibility_under_cent` |
| CENT-013 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_013_margin_calc_order_calc.py::test_cent_013_margin_calc_order_calc` |
| CENT-014 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_014_volume_grid_volume_min.py::test_cent_014_volume_grid_volume_min` |
| CENT-015 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_015_stops_freeze_recorded_converted.py::test_cent_015_stops_freeze_recorded_converted` |
| CENT-016 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_016_account_type_evidence_no.py::test_cent_016_account_type_evidence_no` |
| CENT-017 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_017_tick_sanity_200_consecutive.py::test_cent_017_tick_sanity_200_consecutive` |
| CENT-018 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_018_repeatability_checks_re_run.py::test_cent_018_repeatability_checks_re_run` |
| CENT-020 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_020_re_validation_after_a.py::test_cent_020_re_validation_after_a` |
| CENT-030 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_030_for_each_strategy_and.py::test_cent_030_for_each_strategy_and` |
| CENT-031 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_031_if_the_rate_exceeds.py::test_cent_031_if_the_rate_exceeds` |
| CENT-032 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_032_cgv_06_shows_that.py::test_cent_032_cgv_06_shows_that` |
| CENT-040 | CRITICAL | Live discovery checks + golden vectors | M2–M3 | yes | `tests/integration/test_cent_040_the_m10_pilot_is.py::test_cent_040_the_m10_pilot_is` |
| EXP-001 | CRITICAL | Unit + golden vectors (VER profiles) | M3 |  | `tests/unit/test_exp_001_inputs_from_each_account.py::test_exp_001_inputs_from_each_account` |
| EXP-002 | CRITICAL | Unit + golden vectors (VER profiles) | M3 |  | `tests/unit/test_exp_002_notional_per_position_account.py::test_exp_002_notional_per_position_account` |
| EXP-003 | CRITICAL | Unit + golden vectors (VER profiles) | M3 |  | `tests/unit/test_exp_003_effective_leverage_eff_lev.py::test_exp_003_effective_leverage_eff_lev` |
| EXP-004 | CRITICAL | Unit + golden vectors (VER profiles) | M3 |  | `tests/unit/test_exp_004_margin_utilisation_required_order.py::test_exp_004_margin_utilisation_required_order` |
| EXP-005 | CRITICAL | Unit + golden vectors (VER profiles) | M3 |  | `tests/unit/test_exp_005_projected_margin_level_equity.py::test_exp_005_projected_margin_level_equity` |
| EXP-006 | CRITICAL | Unit + golden vectors (VER profiles) | M3 |  | `tests/unit/test_exp_006_stop_out_distance_report.py::test_exp_006_stop_out_distance_report` |
| EXP-007 | CRITICAL | Unit + golden vectors (VER profiles) | M3 |  | `tests/unit/test_exp_007_account_leverage_cap_account.py::test_exp_007_account_leverage_cap_account` |
| EXP-008 | CRITICAL | Unit + golden vectors (VER profiles) | M3 |  | `tests/unit/test_exp_008_concentration_v1_trades_one.py::test_exp_008_concentration_v1_trades_one` |
| EXP-009 | CRITICAL | Unit + golden vectors (VER profiles) | M3 |  | `tests/unit/test_exp_009_ownership_positions_orders_whose.py::test_exp_009_ownership_positions_orders_whose` |
| MI-061 | CRITICAL | Config schema test + review | M0b/M3 |  | `tests/unit/test_mi_061_risk_profiles_a_risk.py::test_mi_061_risk_profiles_a_risk` |
| RISK-001 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_001_single_authority_riskengine_is.py::test_risk_001_single_authority_riskengine_is` |
| RISK-002 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_002_action_classes_risk_increasing.py::test_risk_002_action_classes_risk_increasing` |
| RISK-003 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_003_determinism_evaluate_is_a.py::test_risk_003_determinism_evaluate_is_a` |
| RISK-004 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_004_re_evaluation_whenever_an.py::test_risk_004_re_evaluation_whenever_an` |
| RISK-005 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_005_pending_parameter_gate_the.py::test_risk_005_pending_parameter_gate_the` |
| RISK-010 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_010_budget_budget_quantize_down.py::test_risk_010_budget_budget_quantize_down` |
| RISK-011 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_011_modelled_loss_per_1.py::test_risk_011_modelled_loss_per_1` |
| RISK-012 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_012_slippage_allowance_slip_per.py::test_risk_012_slippage_allowance_slip_per` |
| RISK-013 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_013_volume_raw_budget_loss.py::test_risk_013_volume_raw_budget_loss` |
| RISK-014 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_014_formula_cross_check_independently.py::test_risk_014_formula_cross_check_independently` |
| RISK-015 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_015_aggregate_open_risk_modelled.py::test_risk_015_aggregate_open_risk_modelled` |
| RISK-016 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_016_strategy_risk_budget_each.py::test_risk_016_strategy_risk_budget_each` |
| RISK-017 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_017_strategy_operating_envelope_every.py::test_risk_017_strategy_operating_envelope_every` |
| RISK-018 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_018_news_policy_a_strategy.py::test_risk_018_news_policy_a_strategy` |
| RISK-020 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_020_boundary_every_float_from.py::test_risk_020_boundary_every_float_from` |
| RISK-021 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_021_decimal_context_use_a.py::test_risk_021_decimal_context_use_a` |
| RISK-022 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_022_rounding_and_price_rules.py::test_risk_022_rounding_and_price_rules` |
| RISK-023 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_023_money_type_money_amount.py::test_risk_023_money_type_money_amount` |
| RISK-024 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_024_values_sent_back_to.py::test_risk_024_values_sent_back_to` |
| RISK-025 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_025_opt_in_price_quantization.py::test_risk_025_opt_in_price_quantization` |
| RISK-030 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_030_sl_required_every_risk.py::test_risk_030_sl_required_every_risk` |
| RISK-031 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_031_broker_confirmed_sl_the.py::test_risk_031_broker_confirmed_sl_the` |
| RISK-032 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_032_distance_rules_abs_entry.py::test_risk_032_distance_rules_abs_entry` |
| RISK-033 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_033_never_widen_no_sl.py::test_risk_033_never_widen_no_sl` |
| RISK-034 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_034_managed_sl_tp_modifications.py::test_risk_034_managed_sl_tp_modifications` |
| RISK-040 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_040_p_02_p_03.py::test_risk_040_p_02_p_03` |
| RISK-041 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_041_no_ui_report_readme.py::test_risk_041_no_ui_report_readme` |
| RISK-042 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_042_reporting_every_intervention_reports.py::test_risk_042_reporting_every_intervention_reports` |
| RISK-050 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_050_manual_recovery_approval_a.py::test_risk_050_manual_recovery_approval_a` |
| RISK-051 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_051_exits_during_states_protective.py::test_risk_051_exits_during_states_protective` |
| RISK-052 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_052_automatic_recovery_rules_only.py::test_risk_052_automatic_recovery_rules_only` |
| RISK-053 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_053_prohibited_automatic_recovery_automatic.py::test_risk_053_prohibited_automatic_recovery_automatic` |
| RISK-060 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_060_the_selected_mode_persists.py::test_risk_060_the_selected_mode_persists` |
| RISK-061 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_061_enabling_an_automatic_mode.py::test_risk_061_enabling_an_automatic_mode` |
| RISK-062 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_062_automatic_demotion_to_human.py::test_risk_062_automatic_demotion_to_human` |
| RISK-063 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_063_promotion_gate_proposed_defaults.py::test_risk_063_promotion_gate_proposed_defaults` |
| RISK-064 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_064_no_mode_can_bypass.py::test_risk_064_no_mode_can_bypass` |
| RISK-065 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_065_fail_closed_while_undecided.py::test_risk_065_fail_closed_while_undecided` |
| RISK-066 | CRITICAL | Unit + golden vectors (GV-33, GV-39, GV-40) | M3/M7 |  | `tests/unit/test_risk_066_fixture_demo_a_demo.py::test_risk_066_fixture_demo_a_demo` |
| RISK-067 | CRITICAL | Unit + golden vector (GV-41) | M3/M9 |  | `tests/unit/test_risk_067_schedule_narrowing_optional_part.py::test_risk_067_schedule_narrowing_optional_part` |
| RISK-090 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_090_config_risk_limits_yaml.py::test_risk_090_config_risk_limits_yaml` |
| RISK-091 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_091_only_the_user_can.py::test_risk_091_only_the_user_can` |
| RISK-092 | CRITICAL | Unit + property + golden vectors | M3 |  | `tests/unit/test_risk_092_approval_record_each_user.py::test_risk_092_approval_record_each_user` |

### M4 (49)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| API-001 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_001_default_bind_127_0.py::test_api_001_default_bind_127_0` |
| API-002 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_002_the_startup_self_check.py::test_api_002_the_startup_self_check` |
| API-003 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_003_security_headers_content_security.py::test_api_003_security_headers_content_security` |
| API-010 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_010_single_local_user_password.py::test_api_010_single_local_user_password` |
| API-011 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_011_login_rate_limit_5.py::test_api_011_login_rate_limit_5` |
| API-012 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_012_csrf_synchronizer_token_header.py::test_api_012_csrf_synchronizer_token_header` |
| API-013 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_013_re_authentication_totp_within.py::test_api_013_re_authentication_totp_within` |
| API-020 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_020_the_engine_re_validates.py::test_api_020_the_engine_re_validates` |
| API-021 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_021_idempotency_every_command_carries.py::test_api_021_idempotency_every_command_carries` |
| API-030 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_030_a_proposal_is_shown.py::test_api_030_a_proposal_is_shown` |
| API-031 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_031_approval_token_hmac_server.py::test_api_031_approval_token_hmac_server` |
| API-033 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_033_approve_buttons_sit_in.py::test_api_033_approve_buttons_sit_in` |
| API-040 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_040_authorization_is_checked_server.py::test_api_040_authorization_is_checked_server` |
| API-050 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_050_get_v1_stream_upgrades.py::test_api_050_get_v1_stream_upgrades` |
| API-051 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_051_every_message_carries_env.py::test_api_051_every_message_carries_env` |
| API-060 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_060_pydantic_models_with_extra.py::test_api_060_pydantic_models_with_extra` |
| API-061 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_061_errors_rfc_9457_style.py::test_api_061_errors_rfc_9457_style` |
| API-062 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_062_rate_limits_per_session.py::test_api_062_rate_limits_per_session` |
| API-063 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_063_audit_every_command_and.py::test_api_063_audit_every_command_and` |
| OBS-001 | CRITICAL | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_001_the_aggregate_status_shown.py::test_obs_001_the_aggregate_status_shown` |
| OBS-002 | CRITICAL | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_002_every_health_computation_has.py::test_obs_002_every_health_computation_has` |
| OBS-010 | HIGH | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_010_json_lines_with_ts.py::test_obs_010_json_lines_with_ts` |
| OBS-011 | HIGH | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_011_levels_debug_dev_only.py::test_obs_011_levels_debug_dev_only` |
| OBS-020 | HIGH | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_020_channels_user_decision_the.py::test_obs_020_channels_user_decision_the` |
| OBS-021 | HIGH | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_021_alert_on_every_critical.py::test_obs_021_alert_on_every_critical` |
| OBS-022 | HIGH | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_022_each_alert_links_to.py::test_obs_022_each_alert_links_to` |
| OBS-023 | CRITICAL | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_023_missed_alert_protection_because.py::test_obs_023_missed_alert_protection_because` |
| UI-001 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_001_layering_watercolor_appears_only.py::test_ui_001_layering_watercolor_appears_only` |
| UI-002 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_002_blur_budget_heavy_blur.py::test_ui_002_blur_budget_heavy_blur` |
| UI-003 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_003_contrast_wcag_2_2.py::test_ui_003_contrast_wcag_2_2` |
| UI-004 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_004_never_colour_alone_every.py::test_ui_004_never_colour_alone_every` |
| UI-005 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_005_numbers_tabular_numerals_every.py::test_ui_005_numbers_tabular_numerals_every` |
| UI-006 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_006_accessibility_fallbacks_prefers_reduced.py::test_ui_006_accessibility_fallbacks_prefers_reduced` |
| UI-007 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_007_performance_60_fps_on.py::test_ui_007_performance_60_fps_on` |
| UI-008 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_008_original_art_only_procedural.py::test_ui_008_original_art_only_procedural` |
| UI-010 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_010_never_green_when_unknown.py::test_ui_010_never_green_when_unknown` |
| UI-011 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_011_freshness_labels_on_every.py::test_ui_011_freshness_labels_on_every` |
| UI-012 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_012_source_labels_position_and.py::test_ui_012_source_labels_position_and` |
| UI-013 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_013_requested_done_emergency_and.py::test_ui_013_requested_done_emergency_and` |
| UI-014 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_014_no_guarantee_language_intervention.py::test_ui_014_no_guarantee_language_intervention` |
| UI-015 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_015_stop_loss_truthfulness_a.py::test_ui_015_stop_loss_truthfulness_a` |
| UI-016 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_016_required_status_vocabulary_market.py::test_ui_016_required_status_vocabulary_market` |
| UI-020 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_020_environment_banner_full_width.py::test_ui_020_environment_banner_full_width` |
| UI-021 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_021_account_risk_panel_balance.py::test_ui_021_account_risk_panel_balance` |
| UI-022 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_022_strategy_panel_strategy_version.py::test_ui_022_strategy_panel_strategy_version` |
| UI-023 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_023_orders_panel_pending_order.py::test_ui_023_orders_panel_pending_order` |
| UI-030 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_030_emergency_controls_user_decision.py::test_ui_030_emergency_controls_user_decision` |
| UI-031 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_031_approval_card_direction_entry.py::test_ui_031_approval_card_direction_entry` |
| UI-032 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_032_entry_authorization_settings_shows.py::test_ui_032_entry_authorization_settings_shows` |

### M5 (25)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| BT-001 | CRITICAL | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_001_every_report_chart_and.py::test_bt_001_every_report_chart_and` |
| BT-002 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_002_pt0_results_may_appear.py::test_bt_002_pt0_results_may_appear` |
| BT-010 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_010_sources_bid_ask_tick.py::test_bt_010_sources_bid_ask_tick` |
| BT-011 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_011_provenance_manifest_per_partition.py::test_bt_011_provenance_manifest_per_partition` |
| BT-012 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_012_quality_checks_results_go.py::test_bt_012_quality_checks_results_go` |
| BT-013 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_013_a_dataset_with_0.py::test_bt_013_a_dataset_with_0` |
| BT-020 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_020_prices_abs_buy_fills.py::test_bt_020_prices_abs_buy_fills` |
| BT-021 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_021_spread_taken_from_each.py::test_bt_021_spread_taken_from_each` |
| BT-022 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_022_costs_commission_per_lot.py::test_bt_022_costs_commission_per_lot` |
| BT-023 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_023_latency_decision_tick_order.py::test_bt_023_latency_decision_tick_order` |
| BT-024 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_024_slippage_market_orders_price.py::test_bt_024_slippage_market_orders_price` |
| BT-025 | CRITICAL | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_025_stop_loss_an_sl.py::test_bt_025_stop_loss_an_sl` |
| BT-026 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_026_take_profit_triggered_when.py::test_bt_026_take_profit_triggered_when` |
| BT-027 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_027_stops_freeze_levels_orders.py::test_bt_027_stops_freeze_levels_orders` |
| BT-028 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_028_rejects_probability_of_reject.py::test_bt_028_rejects_probability_of_reject` |
| BT-029 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_029_partial_fills_prior_probability.py::test_bt_029_partial_fills_prior_probability` |
| BT-030 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_030_sessions_and_closures_no.py::test_bt_030_sessions_and_closures_no` |
| BT-031 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_031_currency_conversion_for_the.py::test_bt_031_currency_conversion_for_the` |
| BT-032 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_032_candle_data_bars_are.py::test_bt_032_candle_data_bars_are` |
| BT-033 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_033_historical_broker_specs_each.py::test_bt_033_historical_broker_specs_each` |
| BT-034 | CRITICAL | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_034_session_end_close_every.py::test_bt_034_session_end_close_every` |
| BT-035 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_035_entry_authorization_delay_when.py::test_bt_035_entry_authorization_delay_when` |
| BT-040 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_040_reproducibility_the_same_data.py::test_bt_040_reproducibility_the_same_data` |
| BT-041 | HIGH | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_041_live_parity_the_m9.py::test_bt_041_live_parity_the_m9` |
| BT-050 | CRITICAL | Micro-scenario + determinism tests | M5 |  | `tests/unit/test_bt_050_shared_core_the_backtester.py::test_bt_050_shared_core_the_backtester` |

### M6 (28)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| RES-001 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_001_hypothesis_plain_language_economic.py::test_res_001_hypothesis_plain_language_economic` |
| RES-002 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_002_pre_registration_research_prereg.py::test_res_002_pre_registration_research_prereg` |
| RES-005 | CRITICAL | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_005_chronological_splits_the_oldest.py::test_res_005_chronological_splits_the_oldest` |
| RES-006 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_006_walk_forward_rolling_windows.py::test_res_006_walk_forward_rolling_windows` |
| RES-007 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_007_purging_and_embargo_s29.py::test_res_007_purging_and_embargo_s29` |
| RES-010 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_010_registry_sqlite_table_experiments.py::test_res_010_registry_sqlite_table_experiments` |
| RES-011 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_011_versioning_any_change_to.py::test_res_011_versioning_any_change_to` |
| RES-012 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_012_nothing_may_be_deleted.py::test_res_012_nothing_may_be_deleted` |
| RES-020 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_020_verdict_pass_fail_inconclusive.py::test_res_020_verdict_pass_fail_inconclusive` |
| RES-021 | CRITICAL | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_021_multiple_testing_every_configuration.py::test_res_021_multiple_testing_every_configuration` |
| RES-022 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_022_no_threshold_shopping_changing.py::test_res_022_no_threshold_shopping_changing` |
| RES-023 | CRITICAL | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_023_strategy_class_is_decided.py::test_res_023_strategy_class_is_decided` |
| RES-024 | CRITICAL | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_024_per_criterion_results_each.py::test_res_024_per_criterion_results_each` |
| RES-025 | CRITICAL | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_025_n_a_rules_no.py::test_res_025_n_a_rules_no` |
| RES-026 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_026_inconclusive_a_criterion_is.py::test_res_026_inconclusive_a_criterion_is` |
| RES-027 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_027_out_of_sample_limitations.py::test_res_027_out_of_sample_limitations` |
| RES-030 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_030_report_performance_by_regime.py::test_res_030_report_performance_by_regime` |
| RES-031 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_031_a_strategy_whose_expectancy.py::test_res_031_a_strategy_whose_expectancy` |
| RES-040 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_040_strategy_states_active_watch.py::test_res_040_strategy_states_active_watch` |
| RES-041 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_041_demotion_is_automatic_promotion.py::test_res_041_demotion_is_automatic_promotion` |
| RES-042 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_042_any_strategy_state_change.py::test_res_042_any_strategy_state_change` |
| RES-050 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_050_win_rate_is_reported.py::test_res_050_win_rate_is_reported` |
| RES-060 | CRITICAL | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_060_only_strategies_with_verdict.py::test_res_060_only_strategies_with_verdict` |
| RES-061 | CRITICAL | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_061_prevalidated_selector_switching_between.py::test_res_061_prevalidated_selector_switching_between` |
| RES-070 | CRITICAL | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_070_operating_envelope_every_strategy.py::test_res_070_operating_envelope_every_strategy` |
| RES-071 | CRITICAL | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_071_news_validation_a_strategy.py::test_res_071_news_validation_a_strategy` |
| RES-072 | CRITICAL | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_072_intraday_only_because_overnight.py::test_res_072_intraday_only_because_overnight` |
| RES-073 | HIGH | Reference-value tests + registry audit | M6 |  | `tests/unit/test_res_073_candidate_proposals_decided_2026.py::test_res_073_candidate_proposals_decided_2026` |

### M6a (14)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| MI-001 | CRITICAL | Static import test + purity tests | M6a |  | `tests/unit/test_mi_001_location_and_purity_the.py::test_mi_001_location_and_purity_the` |
| MI-004 | CRITICAL | Static import test | M6a |  | `tests/unit/test_mi_004_no_llm_in_the.py::test_mi_004_no_llm_in_the` |
| MI-010 | HIGH | Schema + unit tests | M6a |  | `tests/unit/test_mi_010_evidence_record_every_module.py::test_mi_010_evidence_record_every_module` |
| MI-011 | HIGH | Unit tests + wording scan | M6a/M9 |  | `tests/unit/test_mi_011_confidence_is_a_score.py::test_mi_011_confidence_is_a_score` |
| MI-012 | HIGH | Docs check + versioning test | M6a |  | `tests/unit/test_mi_012_objective_versioned_rules_each.py::test_mi_012_objective_versioned_rules_each` |
| MI-013 | CRITICAL | Property test (future truncation) | M6a |  | `tests/property/test_mi_013_no_lookahead_no_repainting.py::test_mi_013_no_lookahead_no_repainting` |
| MI-014 | CRITICAL | Property test (future truncation) | M6a |  | `tests/property/test_mi_014_future_truncation_test_for.py::test_mi_014_future_truncation_test_for` |
| MI-015 | CRITICAL | Unit tests with injected data faults | M6a |  | `tests/unit/test_mi_015_data_quality_fails_closed.py::test_mi_015_data_quality_fails_closed` |
| MI-016 | CRITICAL | Unit tests (bar building, sessions, timestamps) | M6a |  | `tests/unit/test_mi_016_time_and_bars_bars.py::test_mi_016_time_and_bars_bars` |
| MI-018 | CRITICAL | Fault-injection test | M6a/M9 |  | `tests/unit/test_mi_018_module_health_each_module.py::test_mi_018_module_health_each_module` |
| MI-020 | HIGH | Ownership test + unit tests | M6a/M6b |  | `tests/unit/test_mi_020_module_register_there_are.py::test_mi_020_module_register_there_are` |
| MI-030 | HIGH | Unit tests on hand-labelled synthetic bars | M6a |  | `tests/unit/test_mi_030_smart_money_concepts_and.py::test_mi_030_smart_money_concepts_and` |
| MI-031 | HIGH | Unit tests on hand-labelled synthetic bars | M6a |  | `tests/unit/test_mi_031_candlestick_pattern_rules_doji.py::test_mi_031_candlestick_pattern_rules_doji` |
| MI-032 | HIGH | Unit tests | M6a |  | `tests/unit/test_mi_032_pattern_context_without_double.py::test_mi_032_pattern_context_without_double` |

### M6b (15)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| MI-002 | CRITICAL | Integration test (backtester + engine path) | M6b/M9 |  | `tests/integration/test_mi_002_data_flow_market_data.py::test_mi_002_data_flow_market_data` |
| MI-003 | CRITICAL | Static test + property test (confidence never reaches sizing) | M6b |  | `tests/unit/test_mi_003_no_authority_the_intelligence.py::test_mi_003_no_authority_the_intelligence` |
| MI-017 | CRITICAL | Determinism test | M6b |  | `tests/unit/test_mi_017_determinism_the_same_inputs.py::test_mi_017_determinism_the_same_inputs` |
| MI-020 | HIGH | Ownership test + unit tests | M6a/M6b |  | `tests/unit/test_mi_020_module_register_there_are.py::test_mi_020_module_register_there_are` |
| MI-021 | HIGH | Wording scan + review | M6b/M9 |  | `tests/unit/test_mi_021_no_order_flow_claims.py::test_mi_021_no_order_flow_claims` |
| MI-033 | HIGH | Unit tests | M6b |  | `tests/unit/test_mi_033_early_reversal_warning_versus.py::test_mi_033_early_reversal_warning_versus` |
| MI-034 | CRITICAL | Property test (closed higher-timeframe bars) | M6b |  | `tests/property/test_mi_034_multi_timeframe_confluence_uses.py::test_mi_034_multi_timeframe_confluence_uses` |
| MI-035 | HIGH | Reference-value tests against RES-030 | M6b |  | `tests/unit/test_mi_035_regime_labels_the_market.py::test_mi_035_regime_labels_the_market` |
| MI-040 | HIGH | Unit tests | M6b |  | `tests/unit/test_mi_040_inputs_for_one_strategy.py::test_mi_040_inputs_for_one_strategy` |
| MI-041 | HIGH | Unit tests | M6b |  | `tests/unit/test_mi_041_outcomes_exactly_one_of.py::test_mi_041_outcomes_exactly_one_of` |
| MI-042 | CRITICAL | Unit + property tests | M6b |  | `tests/unit/test_mi_042_scoring_and_minimum_confluence.py::test_mi_042_scoring_and_minimum_confluence` |
| MI-043 | CRITICAL | Unit tests + research report | M6b/M6e |  | `tests/unit/test_mi_043_correlation_groups_default_every.py::test_mi_043_correlation_groups_default_every` |
| MI-044 | CRITICAL | Unit tests | M6b |  | `tests/unit/test_mi_044_derived_records_count_once.py::test_mi_044_derived_records_count_once` |
| MI-045 | HIGH | Schema + persistence tests | M6b/M9 |  | `tests/unit/test_mi_045_decision_record_every_decision.py::test_mi_045_decision_record_every_decision` |
| MI-047 | CRITICAL | Unit tests | M6b |  | `tests/unit/test_mi_047_conflicts_and_no_hedging.py::test_mi_047_conflicts_and_no_hedging` |

### M6c (13)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| MI-110 | CRITICAL | Unit + future-truncation tests | M6c |  | `tests/unit/test_mi_110_confirmed_impulse_legs_only.py::test_mi_110_confirmed_impulse_legs_only` |
| MI-111 | HIGH | Reference-value unit tests | M6c |  | `tests/unit/test_mi_111_levels_for_a_bullish.py::test_mi_111_levels_for_a_bullish` |
| MI-112 | HIGH | Unit tests (boundaries) | M6c |  | `tests/unit/test_mi_112_atr_normalised_proximity_price.py::test_mi_112_atr_normalised_proximity_price` |
| MI-113 | HIGH | Unit + closed-bar property tests | M6c |  | `tests/unit/test_mi_113_multi_timeframe_clusters_levels.py::test_mi_113_multi_timeframe_clusters_levels` |
| MI-114 | CRITICAL | Count-once unit test | M6c |  | `tests/unit/test_mi_114_confluence_records_golden_zone.py::test_mi_114_confluence_records_golden_zone` |
| MI-115 | HIGH | Unit tests | M6c |  | `tests/unit/test_mi_115_premium_discount_for_a.py::test_mi_115_premium_discount_for_a` |
| MI-116 | HIGH | Unit tests | M6c |  | `tests/unit/test_mi_116_invalidation_freshness_and_mitigation.py::test_mi_116_invalidation_freshness_and_mitigation` |
| MI-117 | CRITICAL | Unit tests (P-27, RISK-032/034) | M6c |  | `tests/unit/test_mi_117_extension_targets_extension_levels.py::test_mi_117_extension_targets_extension_levels` |
| MI-120 | CRITICAL | Unit + future-truncation tests | M6c |  | `tests/unit/test_mi_120_pivot_framework_every_pattern.py::test_mi_120_pivot_framework_every_pattern` |
| MI-121 | HIGH | Hand-labelled fixtures per table row | M6c |  | `tests/unit/test_mi_121_pattern_rules_research_defaults.py::test_mi_121_pattern_rules_research_defaults` |
| MI-122 | CRITICAL | Unit test (FORMING never supports a candidate) | M6c |  | `tests/unit/test_mi_122_no_trade_from_a.py::test_mi_122_no_trade_from_a` |
| MI-130 | HIGH | Ownership + unit tests | M6c |  | `tests/unit/test_mi_130_ownership_map_no_new.py::test_mi_130_ownership_map_no_new` |
| MI-140 | HIGH | Unit tests (sweep vs wick) | M6c |  | `tests/unit/test_mi_140_confirmed_sweeps_versus_wick.py::test_mi_140_confirmed_sweeps_versus_wick` |

### M6d (23)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| MI-100 | CRITICAL | Registry test (V2.1 versions unchanged) | M6d |  | `tests/unit/test_mi_100_additive_v2_2_v2.py::test_mi_100_additive_v2_2_v2` |
| MI-101 | CRITICAL | Migration up/down test + decision-record equality | M6d |  | `tests/unit/test_mi_101_migration_and_rollback_schema.py::test_mi_101_migration_and_rollback_schema` |
| MI-150 | HIGH | Schema + unit tests | M6d |  | `tests/unit/test_mi_150_one_scorer_a_setup.py::test_mi_150_one_scorer_a_setup` |
| MI-151 | CRITICAL | Group-mapping unit test | M6d |  | `tests/unit/test_mi_151_evidence_categories_map_to.py::test_mi_151_evidence_categories_map_to` |
| MI-152 | CRITICAL | Unit test (fixed priority, no selection) | M6d |  | `tests/unit/test_mi_152_ranking_is_not_selection.py::test_mi_152_ranking_is_not_selection` |
| MI-153 | HIGH | Breakdown-sum unit test | M6d |  | `tests/unit/test_mi_153_every_score_is_explainable.py::test_mi_153_every_score_is_explainable` |
| MI-154 | HIGH | Wording scan + review | M6d/M9 |  | `tests/unit/test_mi_154_thresholds_not_probabilities_high.py::test_mi_154_thresholds_not_probabilities_high` |
| MI-155 | CRITICAL | Static input test | M6d |  | `tests/unit/test_mi_155_no_forced_trades_no.py::test_mi_155_no_forced_trades_no` |
| MI-156 | HIGH | Unit tests | M6d |  | `tests/unit/test_mi_156_prefer_wait_ties_missing.py::test_mi_156_prefer_wait_ties_missing` |
| MI-160 | CRITICAL | Property test (no skipped state) + static test | M6d/M9 |  | `tests/property/test_mi_160_states_every_setup_carries.py::test_mi_160_states_every_setup_carries` |
| MI-170 | HIGH | Unit tests per method | M6d |  | `tests/unit/test_mi_170_three_methods_each_computing.py::test_mi_170_three_methods_each_computing` |
| MI-172 | CRITICAL | FakeBroker + demo integration tests | M6d/M9 | yes | `tests/integration/test_mi_172_safety_existing_rules_restated.py::test_mi_172_safety_existing_rules_restated` |
| MI-173 | CRITICAL | Unit tests (costs, closed bar) | M6d |  | `tests/unit/test_mi_173_net_of_cost_break.py::test_mi_173_net_of_cost_break` |
| MI-174 | CRITICAL | Unit test (minimum volume) | M6d |  | `tests/unit/test_mi_174_partial_exits_need_volume.py::test_mi_174_partial_exits_need_volume` |
| MI-180 | CRITICAL | Static + integration tests (evaluate_* only) | M6d/M9 |  | `tests/unit/test_mi_180_existing_owners_position_sl.py::test_mi_180_existing_owners_position_sl` |
| MI-181 | HIGH | Unit tests | M6d |  | `tests/unit/test_mi_181_exit_conditions_each_used.py::test_mi_181_exit_conditions_each_used` |
| MI-182 | HIGH | Unit tests | M6d |  | `tests/unit/test_mi_182_classification_temporary_retracement_no.py::test_mi_182_classification_temporary_retracement_no` |
| MI-183 | CRITICAL | Unit test (one candle never exits) | M6d |  | `tests/unit/test_mi_183_never_one_candle_a.py::test_mi_183_never_one_candle_a` |
| MI-184 | CRITICAL | Property test (never widens) | M6d/M9 |  | `tests/property/test_mi_184_exits_never_weaken_protection.py::test_mi_184_exits_never_weaken_protection` |
| MI-185 | HIGH | Field-completeness test | M6d/M9 |  | `tests/unit/test_mi_185_every_exit_has_a.py::test_mi_185_every_exit_has_a` |
| MI-190 | CRITICAL | Count-once property test | M6d |  | `tests/property/test_mi_190_timeframe_roles_defaults_d1.py::test_mi_190_timeframe_roles_defaults_d1` |
| MI-191 | HIGH | Unit tests | M6d |  | `tests/unit/test_mi_191_multi_timeframe_detections_higher.py::test_mi_191_multi_timeframe_detections_higher` |
| MI-192 | CRITICAL | Unit tests (gates only block) | M6d |  | `tests/unit/test_mi_192_market_condition_gates_spread.py::test_mi_192_market_condition_gates_spread` |

### M6e (17)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| MI-043 | CRITICAL | Unit tests + research report | M6b/M6e |  | `tests/unit/test_mi_043_correlation_groups_default_every.py::test_mi_043_correlation_groups_default_every` |
| MI-050 | HIGH | Registry audit | M6e |  | `tests/unit/test_mi_050_six_strategy_families_the.py::test_mi_050_six_strategy_families_the` |
| MI-051 | HIGH | Unit + envelope tests | M6e |  | `tests/unit/test_mi_051_regime_dependence_through_the.py::test_mi_051_regime_dependence_through_the` |
| MI-053 | CRITICAL | Unit + backtest tests | M6e |  | `tests/unit/test_mi_053_early_reversal_scalping_strategy.py::test_mi_053_early_reversal_scalping_strategy` |
| MI-060 | CRITICAL | Review + golden vectors | M6e |  | `tests/unit/test_mi_060_mapping_every_risk_item.py::test_mi_060_mapping_every_risk_item` |
| MI-062 | CRITICAL | Unit test (RISK-016) | M6e |  | `tests/unit/test_mi_062_strategy_budgets_each_strategy.py::test_mi_062_strategy_budgets_each_strategy` |
| MI-070 | CRITICAL | Registry audit + report check | M6e |  | `tests/unit/test_mi_070_same_pipeline_no_shortcuts.py::test_mi_070_same_pipeline_no_shortcuts` |
| MI-071 | CRITICAL | Registry trial-count test | M6e |  | `tests/unit/test_mi_071_weights_are_parameters_and.py::test_mi_071_weights_are_parameters_and` |
| MI-072 | HIGH | Report test | M6e |  | `tests/unit/test_mi_072_extra_report_metrics_reported.py::test_mi_072_extra_report_metrics_reported` |
| MI-080 | HIGH | REPLAY field-completeness test | M6e/M9 |  | `tests/integration/test_mi_080_per_trade_explanation_every.py::test_mi_080_per_trade_explanation_every` |
| MI-118 | HIGH | Research report (MI-196) | M6e |  | `tests/unit/test_mi_118_no_inherent_edge_no.py::test_mi_118_no_inherent_edge_no` |
| MI-123 | HIGH | Report test (never a live input) | M6e | yes | `tests/integration/test_mi_123_historical_outcome_tracking_research.py::test_mi_123_historical_outcome_tracking_research` |
| MI-171 | HIGH | Registry trial-count test | M6e |  | `tests/unit/test_mi_171_selection_is_pre_registered.py::test_mi_171_selection_is_pre_registered` |
| MI-175 | HIGH | Backtest report test | M6e |  | `tests/unit/test_mi_175_independent_backtests_each_method.py::test_mi_175_independent_backtests_each_method` |
| MI-196 | CRITICAL | Report test + holdout-touch audit | M6e |  | `tests/unit/test_mi_196_baseline_versus_upgraded_baseline.py::test_mi_196_baseline_versus_upgraded_baseline` |
| MI-197 | HIGH | Unit tests (backtest only) | M6e |  | `tests/unit/test_mi_197_counterfactual_outcome_labels_backtest.py::test_mi_197_counterfactual_outcome_labels_backtest` |
| MI-198 | CRITICAL | CENT tests (existing) | M6e |  | `tests/unit/test_mi_198_cent_account_cent_account.py::test_mi_198_cent_account_cent_account` |

### M6f (2)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| MI-052 | CRITICAL | Registry audit + selector-input test | M6f |  | `tests/unit/test_mi_052_adaptive_strategy_selection_the.py::test_mi_052_adaptive_strategy_selection_the` |
| MI-157 | HIGH | Selector pre-registration audit | M6f |  | `tests/unit/test_mi_157_regime_eligibility_map_research.py::test_mi_157_regime_eligibility_map_research` |

### M7 (68)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| EMG-001 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_emg_001_emergency_liquidate_is_best.py::test_emg_001_emergency_liquidate_is_best` |
| EMG-010 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_emg_010_emergency_sequence_the_supported.py::test_emg_010_emergency_sequence_the_supported` |
| EMG-020 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_emg_020_retry_schedule_per_p.py::test_emg_020_retry_schedule_per_p` |
| EMG-030 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_emg_030_scope_policy_configurable_default.py::test_emg_030_scope_policy_configurable_default` |
| EMG-040 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_emg_040_emergency_actions_run_on.py::test_emg_040_emergency_actions_run_on` |
| EXE-001 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_001_a_request_is_not.py::test_exe_001_a_request_is_not` |
| EXE-002 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_002_idempotency_and_duplicate_prevention.py::test_exe_002_idempotency_and_duplicate_prevention` |
| EXE-003 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_003_single_writer_only_the.py::test_exe_003_single_writer_only_the` |
| EXE-004 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_004_fail_closed_these_conditions.py::test_exe_004_fail_closed_these_conditions` |
| EXE-010 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_010_order_check_runs_before.py::test_exe_010_order_check_runs_before` |
| EXE-011 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_011_entries_are_never_blindly.py::test_exe_011_entries_are_never_blindly` |
| EXE-012 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_012_when_the_entry_needs.py::test_exe_012_when_the_entry_needs` |
| EXE-013 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_013_timeouts_are_not_failures.py::test_exe_013_timeouts_are_not_failures` |
| EXE-014 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_014_reconciling_an_unknown_operation.py::test_exe_014_reconciling_an_unknown_operation` |
| EXE-015 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_015_final_states_completed_closed.py::test_exe_015_final_states_completed_closed` |
| EXE-020 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_020_fields_action_symbol_volume.py::test_exe_020_fields_action_symbol_volume` |
| EXE-021 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_021_comment_field_length_and.py::test_exe_021_comment_field_length_and` |
| EXE-022 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_022_magic_numbers_magic_engine.py::test_exe_022_magic_numbers_magic_engine` |
| EXE-030 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_030_after_a_fill_read.py::test_exe_030_after_a_fill_read` |
| EXE-031 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_031_if_the_sl_is.py::test_exe_031_if_the_sl_is` |
| EXE-040 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_040_a_partial_fill_is.py::test_exe_040_a_partial_fill_is` |
| EXE-041 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_041_partial_closes_during_an.py::test_exe_041_partial_closes_during_an` |
| EXE-050 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_050_runs_on_start_after.py::test_exe_050_runs_on_start_after` |
| EXE-051 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_051_mismatch_types_missing_at.py::test_exe_051_mismatch_types_missing_at` |
| EXE-052 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_052_reconciliation_never_trades_to.py::test_exe_052_reconciliation_never_trades_to` |
| EXE-060 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_060_tracked_per_session_fill.py::test_exe_060_tracked_per_session_fill` |
| EXE-070 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_070_startup_sequence_load_and.py::test_exe_070_startup_sequence_load_and` |
| EXE-071 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_071_after_an_unclean_restart.py::test_exe_071_after_an_unclean_restart` |
| EXE-072 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_072_broker_maintenance_and_weekends.py::test_exe_072_broker_maintenance_and_weekends` |
| EXE-080 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_080_session_calendar_session_ends.py::test_exe_080_session_calendar_session_ends` |
| EXE-081 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_081_pre_close_entry_restriction.py::test_exe_081_pre_close_entry_restriction` |
| EXE-082 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_082_pending_orders_at_the.py::test_exe_082_pending_orders_at_the` |
| EXE-083 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_083_close_deadline_at_p.py::test_exe_083_close_deadline_at_p` |
| EXE-084 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_084_failed_close_escalation_if.py::test_exe_084_failed_close_escalation_if` |
| EXE-085 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_085_weekend_protection_the_final.py::test_exe_085_weekend_protection_the_final` |
| EXE-086 | CRITICAL | FakeBroker integration + demo chaos | M7 | yes | `tests/integration/test_exe_086_disconnection_near_the_close.py::test_exe_086_disconnection_near_the_close` |
| GRD-001 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_001_the_guardian_is_an.py::test_grd_001_the_guardian_is_an` |
| GRD-002 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_002_hard_limits_come_from.py::test_grd_002_hard_limits_come_from` |
| GRD-003 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_003_the_engine_s_guardian.py::test_grd_003_the_engine_s_guardian` |
| GRD-004 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_004_the_guardian_never_opens.py::test_grd_004_the_guardian_never_opens` |
| GRD-005 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_005_size_target_1_000.py::test_grd_005_size_target_1_000` |
| GRD-006 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_006_atomic_write_the_writer.py::test_grd_006_atomic_write_the_writer` |
| GRD-007 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_007_reader_rules_open_with.py::test_grd_007_reader_rules_open_with` |
| GRD-008 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_008_channel_integrity_without_a.py::test_grd_008_channel_integrity_without_a` |
| GRD-010 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_010_the_engine_writes_engine.py::test_grd_010_the_engine_writes_engine` |
| GRD-011 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_011_the_guardian_writes_guardian.py::test_grd_011_the_guardian_writes_guardian` |
| GRD-012 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_012_staleness_the_guardian_considers.py::test_grd_012_staleness_the_guardian_considers` |
| GRD-013 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_013_if_the_engine_s.py::test_grd_013_if_the_engine_s` |
| GRD-015 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_015_when_the_engine_is.py::test_grd_015_when_the_engine_is` |
| GRD-016 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_016_clearing_the_guardian_s.py::test_grd_016_clearing_the_guardian_s` |
| GRD-018 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_018_positions_with_magic_magic.py::test_grd_018_positions_with_magic_magic` |
| GRD-019 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_019_every_guardian_trade_request.py::test_grd_019_every_guardian_trade_request` |
| GRD-020 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_020_missing_stop_response_within.py::test_grd_020_missing_stop_response_within` |
| GRD-021 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_021_the_guardian_never_moves.py::test_grd_021_the_guardian_never_moves` |
| GRD-025 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_025_the_guardian_keeps_its.py::test_grd_025_the_guardian_keeps_its` |
| GRD-026 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_026_when_equity_loss_its.py::test_grd_026_when_equity_loss_its` |
| GRD-027 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_027_on_restart_oninit_load.py::test_grd_027_on_restart_oninit_load` |
| GRD-028 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_028_session_end_backstop_if.py::test_grd_028_session_end_backstop_if` |
| GRD-030 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_030_all_documentation_and_ui.py::test_grd_030_all_documentation_and_ui` |
| GRD-031 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_031_guardian_failure_detection_by.py::test_grd_031_guardian_failure_detection_by` |
| GRD-032 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_032_audit_every_guardian_decision.py::test_grd_032_audit_every_guardian_decision` |
| GRD-033 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_033_terminal_disconnected_terminal_connected.py::test_grd_033_terminal_disconnected_terminal_connected` |
| GRD-040 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_040_takeover_reporting_any_guardian.py::test_grd_040_takeover_reporting_any_guardian` |
| GRD-041 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_041_sessions_calendar_weekly_export.py::test_grd_041_sessions_calendar_weekly_export` |
| GRD-050 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_050_lease_when_the_engine.py::test_grd_050_lease_when_the_engine` |
| GRD-051 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_051_check_then_act_before.py::test_grd_051_check_then_act_before` |
| GRD-052 | CRITICAL | MQL5 test script + demo scenarios | M7 (heartbeat/time in M2) | yes | `tests/integration/test_grd_052_sl_placement_by_the.py::test_grd_052_sl_placement_by_the` |
| RISK-066 | CRITICAL | Unit + golden vectors (GV-33, GV-39, GV-40) | M3/M7 |  | `tests/unit/test_risk_066_fixture_demo_a_demo.py::test_risk_066_fixture_demo_a_demo` |

### M8 (87)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| API-001 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_001_default_bind_127_0.py::test_api_001_default_bind_127_0` |
| API-002 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_002_the_startup_self_check.py::test_api_002_the_startup_self_check` |
| API-003 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_003_security_headers_content_security.py::test_api_003_security_headers_content_security` |
| API-010 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_010_single_local_user_password.py::test_api_010_single_local_user_password` |
| API-011 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_011_login_rate_limit_5.py::test_api_011_login_rate_limit_5` |
| API-012 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_012_csrf_synchronizer_token_header.py::test_api_012_csrf_synchronizer_token_header` |
| API-013 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_013_re_authentication_totp_within.py::test_api_013_re_authentication_totp_within` |
| API-020 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_020_the_engine_re_validates.py::test_api_020_the_engine_re_validates` |
| API-021 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_021_idempotency_every_command_carries.py::test_api_021_idempotency_every_command_carries` |
| API-030 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_030_a_proposal_is_shown.py::test_api_030_a_proposal_is_shown` |
| API-031 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_031_approval_token_hmac_server.py::test_api_031_approval_token_hmac_server` |
| API-033 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_033_approve_buttons_sit_in.py::test_api_033_approve_buttons_sit_in` |
| API-040 | CRITICAL | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_040_authorization_is_checked_server.py::test_api_040_authorization_is_checked_server` |
| API-050 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_050_get_v1_stream_upgrades.py::test_api_050_get_v1_stream_upgrades` |
| API-051 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_051_every_message_carries_env.py::test_api_051_every_message_carries_env` |
| API-060 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_060_pydantic_models_with_extra.py::test_api_060_pydantic_models_with_extra` |
| API-061 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_061_errors_rfc_9457_style.py::test_api_061_errors_rfc_9457_style` |
| API-062 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_062_rate_limits_per_session.py::test_api_062_rate_limits_per_session` |
| API-063 | HIGH | Route × scope matrix + security tests | M4/M8 |  | `tests/security/test_api_063_audit_every_command_and.py::test_api_063_audit_every_command_and` |
| LLM-001 | CRITICAL | Static import test + payload tests | M8 |  | `tests/unit/test_llm_001_no_llm_output_can.py::test_llm_001_no_llm_output_can` |
| LLM-002 | CRITICAL | Static import test + payload tests | M8 |  | `tests/unit/test_llm_002_permitted_uses_drafting_research.py::test_llm_002_permitted_uses_drafting_research` |
| LLM-003 | CRITICAL | Static import test + payload tests | M8 |  | `tests/unit/test_llm_003_inputs_follow_prv_020.py::test_llm_003_inputs_follow_prv_020` |
| LLM-004 | CRITICAL | Static import test + payload tests | M8 |  | `tests/unit/test_llm_004_disabled_by_default_when.py::test_llm_004_disabled_by_default_when` |
| LLM-005 | CRITICAL | Static import test + payload tests | M8 |  | `tests/unit/test_llm_005_the_trade_proposal_rationale.py::test_llm_005_the_trade_proposal_rationale` |
| LLM-006 | CRITICAL | Static import test + payload tests | M8 |  | `tests/unit/test_llm_006_no_ai_dependency_for.py::test_llm_006_no_ai_dependency_for` |
| MCP-001 | HIGH | MCP security tests | M8 |  | `tests/security/test_mcp_001_the_mcp_server_is.py::test_mcp_001_the_mcp_server_is` |
| MCP-002 | HIGH | MCP security tests | M8 |  | `tests/security/test_mcp_002_not_to_be_confused.py::test_mcp_002_not_to_be_confused` |
| MCP-005 | CRITICAL | MCP security tests | M8 |  | `tests/security/test_mcp_005_transport_local_stdio_only.py::test_mcp_005_transport_local_stdio_only` |
| MCP-006 | CRITICAL | MCP security tests | M8 |  | `tests/security/test_mcp_006_credentials_per_the_mcp.py::test_mcp_006_credentials_per_the_mcp` |
| MCP-007 | CRITICAL | MCP security tests | M8 |  | `tests/security/test_mcp_007_network_transport_not_in.py::test_mcp_007_network_transport_not_in` |
| MCP-010 | CRITICAL | MCP security tests | M8 |  | `tests/security/test_mcp_010_no_mcp_tool_resource.py::test_mcp_010_no_mcp_tool_resource` |
| MCP-011 | CRITICAL | MCP security tests | M8 |  | `tests/security/test_mcp_011_enforcement_in_depth_1.py::test_mcp_011_enforcement_in_depth_1` |
| MCP-015 | HIGH | MCP security tests | M8 |  | `tests/security/test_mcp_015_validation_strict_schema_validation.py::test_mcp_015_validation_strict_schema_validation` |
| MCP-016 | CRITICAL | MCP security tests | M8 |  | `tests/security/test_mcp_016_adding_any_other_admin.py::test_mcp_016_adding_any_other_admin` |
| MCP-020 | CRITICAL | MCP security tests | M8 |  | `tests/security/test_mcp_020_the_api_checks_every.py::test_mcp_020_the_api_checks_every` |
| MCP-021 | CRITICAL | MCP security tests | M8 |  | `tests/security/test_mcp_021_client_identity_what_is.py::test_mcp_021_client_identity_what_is` |
| MCP-022 | CRITICAL | MCP security tests | M8 |  | `tests/security/test_mcp_022_same_windows_user_limits.py::test_mcp_022_same_windows_user_limits` |
| MCP-023 | CRITICAL | MCP security tests | M8 |  | `tests/security/test_mcp_023_unauthorized_clients_an_unknown.py::test_mcp_023_unauthorized_clients_an_unknown` |
| MCP-024 | CRITICAL | MCP security tests | M8 |  | `tests/security/test_mcp_024_revocation_disabling_a_client.py::test_mcp_024_revocation_disabling_a_client` |
| MCP-030 | CRITICAL | MCP security tests | M8 |  | `tests/security/test_mcp_030_client_registration_and_consent.py::test_mcp_030_client_registration_and_consent` |
| MCP-031 | HIGH | MCP security tests | M8 |  | `tests/security/test_mcp_031_client_trust_boundary_the.py::test_mcp_031_client_trust_boundary_the` |
| MCP-035 | HIGH | MCP security tests | M8 |  | `tests/security/test_mcp_035_rate_limits_30_calls.py::test_mcp_035_rate_limits_30_calls` |
| MCP-040 | CRITICAL | MCP security tests | M8 |  | `tests/security/test_mcp_040_redaction_no_c4_data.py::test_mcp_040_redaction_no_c4_data` |
| MCP-041 | HIGH | MCP security tests | M8 |  | `tests/security/test_mcp_041_prompt_injection_defence_outputs.py::test_mcp_041_prompt_injection_defence_outputs` |
| MCP-042 | HIGH | MCP security tests | M8 |  | `tests/security/test_mcp_042_errors_are_generic_error.py::test_mcp_042_errors_are_generic_error` |
| MCP-045 | HIGH | MCP security tests | M8 |  | `tests/security/test_mcp_045_every_call_is_audited.py::test_mcp_045_every_call_is_audited` |
| MCP-050 | HIGH | MCP security tests | M8 |  | `tests/security/test_mcp_050_failure_behaviour_mcp_server.py::test_mcp_050_failure_behaviour_mcp_server` |
| MCP-060 | HIGH | MCP security tests | M8 |  | `tests/security/test_mcp_060_security_tests_m8_call.py::test_mcp_060_security_tests_m8_call` |
| PRV-001 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_001_local_first_all_operational.py::test_prv_001_local_first_all_operational` |
| PRV-002 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_002_minimisation_collect_only_what.py::test_prv_002_minimisation_collect_only_what` |
| PRV-003 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_003_telemetry_off_no_usage.py::test_prv_003_telemetry_off_no_usage` |
| PRV-004 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_004_explicit_consent_for_every.py::test_prv_004_explicit_consent_for_every` |
| PRV-010 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_010_each_sqlite_table_and.py::test_prv_010_each_sqlite_table_and` |
| PRV-011 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_011_the_account_login_appears.py::test_prv_011_the_account_login_appears` |
| PRV-012 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_012_local_salt_lifecycle.py::test_prv_012_local_salt_lifecycle` |
| PRV-013 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_013_deletion_vs_hash_chained.py::test_prv_013_deletion_vs_hash_chained` |
| PRV-014 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_014_partial_deletion_request_e.py::test_prv_014_partial_deletion_request_e` |
| PRV-015 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_015_full_deletion_workflow_goldbot.py::test_prv_015_full_deletion_workflow_goldbot` |
| PRV-016 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_016_export_workflow_goldbot_privacy.py::test_prv_016_export_workflow_goldbot_privacy` |
| PRV-018 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_018_consent_can_be_withdrawn.py::test_prv_018_consent_can_be_withdrawn` |
| PRV-020 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_020_what_may_be_shared.py::test_prv_020_what_may_be_shared` |
| PRV-021 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_021_prompt_construction_goes_through.py::test_prv_021_prompt_construction_goes_through` |
| PRV-022 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_022_responses_are_stored_30.py::test_prv_022_responses_are_stored_30` |
| PRV-023 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_023_provider_disclosure_and_consent.py::test_prv_023_provider_disclosure_and_consent` |
| PRV-024 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_024_what_must_never_be.py::test_prv_024_what_must_never_be` |
| PRV-025 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_025_sanitisation_build_llm_payload.py::test_prv_025_sanitisation_build_llm_payload` |
| PRV-026 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_026_provider_unavailable_ai_features.py::test_prv_026_provider_unavailable_ai_features` |
| PRV-030 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_030_daily_encrypted_backup_e.py::test_prv_030_daily_encrypted_backup_e` |
| PRV-031 | CRITICAL | Privacy tests + inspection | M8 |  | `tests/security/test_prv_031_restore_test_monthly_automated.py::test_prv_031_restore_test_monthly_automated` |
| SEC-001 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_001_secrets_live_in_the.py::test_sec_001_secrets_live_in_the` |
| SEC-002 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_002_the_investor_password_is.py::test_sec_002_the_investor_password_is` |
| SEC-003 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_003_goldbot_never_asks_for.py::test_sec_003_goldbot_never_asks_for` |
| SEC-004 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_004_redaction_a_logging_filter.py::test_sec_004_redaction_a_logging_filter` |
| SEC-005 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_005_pre_commit_gitleaks_a.py::test_sec_005_pre_commit_gitleaks_a` |
| SEC-006 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_006_separate_permissions_monitoring_investor.py::test_sec_006_separate_permissions_monitoring_investor` |
| SEC-007 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_007_credential_compromise_response_t24.py::test_sec_007_credential_compromise_response_t24` |
| SEC-010 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_010_host_dedicated_windows_user.py::test_sec_010_host_dedicated_windows_user` |
| SEC-011 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_011_network_the_api_binds.py::test_sec_011_network_the_api_binds` |
| SEC-012 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_012_dependencies_uv_lock_pnpm.py::test_sec_012_dependencies_uv_lock_pnpm` |
| SEC-013 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_013_builds_ci_runs_lint.py::test_sec_013_builds_ci_runs_lint` |
| SEC-020 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_020_risk_limits_yaml_hash.py::test_sec_020_risk_limits_yaml_hash` |
| SEC-021 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_021_approval_tokens_hmac_over.py::test_sec_021_approval_tokens_hmac_over` |
| SEC-022 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_022_audit_log_append_only.py::test_sec_022_audit_log_append_only` |
| SEC-023 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_023_commands_approve_mode_change.py::test_sec_023_commands_approve_mode_change` |
| SEC-030 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_030_llm_inputs_are_built.py::test_sec_030_llm_inputs_are_built` |
| SEC-031 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_031_llm_outputs_are_parsed.py::test_sec_031_llm_outputs_are_parsed` |
| SEC-032 | CRITICAL | Security tests + review | M1/M8 |  | `tests/security/test_sec_032_calendar_news_data_is.py::test_sec_032_calendar_news_data_is` |

### M9 (49)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| MI-002 | CRITICAL | Integration test (backtester + engine path) | M6b/M9 |  | `tests/integration/test_mi_002_data_flow_market_data.py::test_mi_002_data_flow_market_data` |
| MI-011 | HIGH | Unit tests + wording scan | M6a/M9 |  | `tests/unit/test_mi_011_confidence_is_a_score.py::test_mi_011_confidence_is_a_score` |
| MI-018 | CRITICAL | Fault-injection test | M6a/M9 |  | `tests/unit/test_mi_018_module_health_each_module.py::test_mi_018_module_health_each_module` |
| MI-021 | HIGH | Wording scan + review | M6b/M9 |  | `tests/unit/test_mi_021_no_order_flow_claims.py::test_mi_021_no_order_flow_claims` |
| MI-045 | HIGH | Schema + persistence tests | M6b/M9 |  | `tests/unit/test_mi_045_decision_record_every_decision.py::test_mi_045_decision_record_every_decision` |
| MI-046 | CRITICAL | Integration test | M9 |  | `tests/integration/test_mi_046_downstream_gates_are_unchanged.py::test_mi_046_downstream_gates_are_unchanged` |
| MI-080 | HIGH | REPLAY field-completeness test | M6e/M9 |  | `tests/integration/test_mi_080_per_trade_explanation_every.py::test_mi_080_per_trade_explanation_every` |
| MI-081 | HIGH | Playwright + axe + UNKNOWN-state tests | M9 |  | `tests/e2e/test_mi_081_dashboard_additions_built_in.py::test_mi_081_dashboard_additions_built_in` |
| MI-082 | HIGH | Playwright + wording scan | M9 |  | `tests/e2e/test_mi_082_honest_labels_chart_overlays.py::test_mi_082_honest_labels_chart_overlays` |
| MI-154 | HIGH | Wording scan + review | M6d/M9 |  | `tests/unit/test_mi_154_thresholds_not_probabilities_high.py::test_mi_154_thresholds_not_probabilities_high` |
| MI-160 | CRITICAL | Property test (no skipped state) + static test | M6d/M9 |  | `tests/property/test_mi_160_states_every_setup_carries.py::test_mi_160_states_every_setup_carries` |
| MI-161 | CRITICAL | Integration test (each requirement blocks) | M9 |  | `tests/integration/test_mi_161_autonomous_entry_requirements_execution.py::test_mi_161_autonomous_entry_requirements_execution` |
| MI-172 | CRITICAL | FakeBroker + demo integration tests | M6d/M9 | yes | `tests/integration/test_mi_172_safety_existing_rules_restated.py::test_mi_172_safety_existing_rules_restated` |
| MI-180 | CRITICAL | Static + integration tests (evaluate_* only) | M6d/M9 |  | `tests/unit/test_mi_180_existing_owners_position_sl.py::test_mi_180_existing_owners_position_sl` |
| MI-184 | CRITICAL | Property test (never widens) | M6d/M9 |  | `tests/property/test_mi_184_exits_never_weaken_protection.py::test_mi_184_exits_never_weaken_protection` |
| MI-185 | HIGH | Field-completeness test | M6d/M9 |  | `tests/unit/test_mi_185_every_exit_has_a.py::test_mi_185_every_exit_has_a` |
| MI-195 | HIGH | Playwright + axe + UNKNOWN-state tests | M9 |  | `tests/e2e/test_mi_195_ten_views_in_the.py::test_mi_195_ten_views_in_the` |
| OBS-001 | CRITICAL | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_001_the_aggregate_status_shown.py::test_obs_001_the_aggregate_status_shown` |
| OBS-002 | CRITICAL | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_002_every_health_computation_has.py::test_obs_002_every_health_computation_has` |
| OBS-010 | HIGH | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_010_json_lines_with_ts.py::test_obs_010_json_lines_with_ts` |
| OBS-011 | HIGH | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_011_levels_debug_dev_only.py::test_obs_011_levels_debug_dev_only` |
| OBS-020 | HIGH | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_020_channels_user_decision_the.py::test_obs_020_channels_user_decision_the` |
| OBS-021 | HIGH | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_021_alert_on_every_critical.py::test_obs_021_alert_on_every_critical` |
| OBS-022 | HIGH | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_022_each_alert_links_to.py::test_obs_022_each_alert_links_to` |
| OBS-023 | CRITICAL | Health-state unit tests + M9 targets | M4/M9 |  | `tests/unit/test_obs_023_missed_alert_protection_because.py::test_obs_023_missed_alert_protection_because` |
| OBS-024 | HIGH | E2E (Playwright) + privacy check | M9 |  | `tests/e2e/test_obs_024_approval_notifications_whenever_an.py::test_obs_024_approval_notifications_whenever_an` |
| RISK-067 | CRITICAL | Unit + golden vector (GV-41) | M3/M9 |  | `tests/unit/test_risk_067_schedule_narrowing_optional_part.py::test_risk_067_schedule_narrowing_optional_part` |
| UI-001 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_001_layering_watercolor_appears_only.py::test_ui_001_layering_watercolor_appears_only` |
| UI-002 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_002_blur_budget_heavy_blur.py::test_ui_002_blur_budget_heavy_blur` |
| UI-003 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_003_contrast_wcag_2_2.py::test_ui_003_contrast_wcag_2_2` |
| UI-004 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_004_never_colour_alone_every.py::test_ui_004_never_colour_alone_every` |
| UI-005 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_005_numbers_tabular_numerals_every.py::test_ui_005_numbers_tabular_numerals_every` |
| UI-006 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_006_accessibility_fallbacks_prefers_reduced.py::test_ui_006_accessibility_fallbacks_prefers_reduced` |
| UI-007 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_007_performance_60_fps_on.py::test_ui_007_performance_60_fps_on` |
| UI-008 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_008_original_art_only_procedural.py::test_ui_008_original_art_only_procedural` |
| UI-010 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_010_never_green_when_unknown.py::test_ui_010_never_green_when_unknown` |
| UI-011 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_011_freshness_labels_on_every.py::test_ui_011_freshness_labels_on_every` |
| UI-012 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_012_source_labels_position_and.py::test_ui_012_source_labels_position_and` |
| UI-013 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_013_requested_done_emergency_and.py::test_ui_013_requested_done_emergency_and` |
| UI-014 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_014_no_guarantee_language_intervention.py::test_ui_014_no_guarantee_language_intervention` |
| UI-015 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_015_stop_loss_truthfulness_a.py::test_ui_015_stop_loss_truthfulness_a` |
| UI-016 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_016_required_status_vocabulary_market.py::test_ui_016_required_status_vocabulary_market` |
| UI-020 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_020_environment_banner_full_width.py::test_ui_020_environment_banner_full_width` |
| UI-021 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_021_account_risk_panel_balance.py::test_ui_021_account_risk_panel_balance` |
| UI-022 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_022_strategy_panel_strategy_version.py::test_ui_022_strategy_panel_strategy_version` |
| UI-023 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_023_orders_panel_pending_order.py::test_ui_023_orders_panel_pending_order` |
| UI-030 | CRITICAL | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_030_emergency_controls_user_decision.py::test_ui_030_emergency_controls_user_decision` |
| UI-031 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_031_approval_card_direction_entry.py::test_ui_031_approval_card_direction_entry` |
| UI-032 | HIGH | Playwright + axe + visual snapshots | M4/M9 |  | `tests/e2e/test_ui_032_entry_authorization_settings_shows.py::test_ui_032_entry_authorization_settings_shows` |

### EACH (checked by the 02 review in every milestone) (10)

| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |
| --- | --- | --- | --- | --- | --- |
| GOV-001 | CRITICAL | Review (02 prompt) + STATUS audit | each milestone (02 review) |  | REVIEW (no automated test) |
| GOV-002 | CRITICAL | Review (02 prompt) + STATUS audit | each milestone (02 review) |  | REVIEW (no automated test) |
| GOV-003 | CRITICAL | Review (02 prompt) + STATUS audit | each milestone (02 review) |  | REVIEW (no automated test) |
| GOV-004 | HIGH | Review (02 prompt) + STATUS audit | each milestone (02 review) |  | REVIEW (no automated test) |
| MI-090 | HIGH | Review (02 prompt) + STATUS audit | each milestone (02 review) |  | REVIEW (no automated test) |
| MI-091 | HIGH | Review (02 prompt) + STATUS audit | each milestone (02 review) |  | REVIEW (no automated test) |
| MI-092 | HIGH | Review (02 prompt) + CI | each milestone (02 review) |  | REVIEW (no automated test) |
| MI-093 | CRITICAL | 03 prompt evidence table | each milestone (02 review) |  | REVIEW (no automated test) |
| MI-162 | CRITICAL | Review (02 check 47) + config audit | each milestone (02 review) |  | `tests/unit/test_mi_162_auto_all_intent_the.py::test_mi_162_auto_all_intent_the` |
| MI-199 | HIGH | STATUS audit | each milestone (02 review) |  | REVIEW (no automated test) |

## 5. Guardian `[HUMAN]` steps (GUARDIAN_SAFETY_SPEC §13; M2 observer and M7b)

The builder pauses and asks the user for each step. A `[HUMAN]` test passes only with the
evidence listed (GOV-002). Step names are parsed from §13; the folder-ACL change and the
duplicate-engine test are scripted, not `[HUMAN]`.

| # | `[HUMAN]` step (§13) | Instruction for the user | Evidence to collect |
| --- | --- | --- | --- |
| H1 | attaching the EA and setting its inputs | In the MT5 terminal, attach the Guardian EA to one chart of the selected symbol and type in every input value the builder gives (equal to or tighter than the approved P-xx, GRD-013). Leave `rearm_counter` as it is. | `guardian_hb.json` with `config_status` = `OK` and `effective_limits` equal to the typed inputs; a screenshot of the EA Inputs tab. |
| H2 | changing `rearm_counter` | After the builder's scenario has set a kill flag that needs a re-arm (GRD-016), open the EA inputs, increase `rearm_counter` by one and confirm. | Guardian heartbeat before (flag set, with its reason) and after (flag cleared), and the `guardian_audit.jsonl` record of the re-arm. |
| H3 | removing an SL by hand | On the Standard demo, with the builder's minimum-size test position open, clear its stop-loss in the terminal (Modify position, empty S/L) and wait 30 s. | The Guardian audit record of the budget-compliant SL it placed after the grace period with its `OrderCalcProfit` loss <= L (GRD-020), and the broker read-back of the new SL. |
| H4 | tightening the daily-loss input to 0.01% | Demo only: with a test position open, set the Guardian daily-loss input to 0.01% and confirm. Restore the previous value when the builder says the scenario is over. | Guardian heartbeat with `takeover` = true and the last action, the close in the terminal's history, and the engine's T18 record (GRD-026, GRD-031). |
| H5 | removing the EA | Remove the Guardian EA from its chart while the engine runs. Note the clock time. | The Guardian's final heartbeat with the deinit reason, and the engine's T9 record with a timestamp at most 20 s after the removal (GRD-012, GRD-031). |
| H6 | disconnecting the terminal | Disconnect the computer from the network for about 60 s, then reconnect. | Guardian audit records of the latched kill flag and of the SL and equity re-verification after reconnect (GRD-033), and the engine's DISCONNECTED and reconnect records. |

## 6. UNMAPPED requirements

None: every requirement has a test type and at least one milestone.
