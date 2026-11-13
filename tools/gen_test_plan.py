#!/usr/bin/env python3
"""Generate docs/TEST_PLAN.md from the traceability matrix and GUARDIAN_SAFETY_SPEC.md section 13.

Usage:
    python tools/gen_test_plan.py              write docs/TEST_PLAN.md
    python tools/gen_test_plan.py --check      exit 1 if docs/TEST_PLAN.md is out of date
    python tools/gen_test_plan.py --self-test  run the parser assertions on inline tables

Standard library only. Output is deterministic and uses LF line endings.
Exit codes: 0 ok, 1 stale (--check), 2 conflicting duplicate IDs or unparseable sources.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACE = ROOT / "quality" / "REQUIREMENTS_TRACEABILITY.md"
GUARDIAN = ROOT / "specifications" / "GUARDIAN_SAFETY_SPEC.md"
OUT = ROOT / "docs" / "TEST_PLAN.md"

UNMAPPED = "UNMAPPED"
EACH = "EACH"  # acceptance criterion says the 02 review checks it every milestone

# Area = first rule whose keyword occurs in the first "+"-separated part of the Verification
# cell (the primary test). Areas are the tests/ folders of the M1 layout.
AREA_RULES: tuple[tuple[str, str], ...] = (
    ("playwright", "e2e"),
    ("e2e", "e2e"),
    ("security", "security"),
    ("privacy", "security"),
    ("route", "security"),
    ("chaos", "chaos"),
    ("mql5", "integration"),
    ("fakebroker", "integration"),
    ("integration", "integration"),
    ("live", "integration"),
    ("demo", "integration"),
    ("replay", "integration"),
    ("golden", "golden"),
    ("property", "property"),
    ("truncation", "property"),
)
DEFAULT_AREA = "unit"
MT5_KEYWORDS = ("live", "demo", "mql5")

# Process/review-only rows: a row is verified by a review or a human step, not by a pytest file,
# when EVERY "+"-separated part of its Verification cell matches one of these markers (regex,
# case-insensitive). A pytest name for such a row could only hold a tautological test. One
# automated part (e.g. "Security tests + review", "Review (02 check 47) + config audit") keeps
# the pytest name for that part.
PROCESS_MARKERS: tuple[str, ...] = (
    r"\breview\b",
    r"\bstatus audit\b",
    r"\bevidence table\b",
    r"\binspection\b",
    r"\bmanual\b",
    r"\bdocument\b",
    r"\bci\b",
    r"\[human\]",
)
HUMAN_MARKER = "[human]"
REVIEW_TEST = "REVIEW (no automated test)"
HUMAN_TEST = "HUMAN step"

# [HUMAN] steps: the step names are parsed from GUARDIAN_SAFETY_SPEC.md section 13. The user
# instruction and the evidence below are the plan's own wording, keyed by the parsed name; a
# parsed step without an entry here stops the generator, so a spec change cannot go unnoticed.
HUMAN_DETAILS: dict[str, tuple[str, str]] = {
    "attaching the EA and setting its inputs": (
        (
            "In the MT5 terminal, attach the Guardian EA to one chart of the selected symbol and type "
            "in every input value the builder gives (equal to or tighter than the approved P-xx, "
            "GRD-013). Leave `rearm_counter` as it is."
        ),
        (
            "`guardian_hb.json` with `config_status` = `OK` and `effective_limits` equal to the typed "
            "inputs; a screenshot of the EA Inputs tab."
        ),
    ),
    "changing `rearm_counter`": (
        (
            "After the builder's scenario has set a kill flag that needs a re-arm (GRD-016), open the "
            "EA inputs, increase `rearm_counter` by one and confirm."
        ),
        (
            "Guardian heartbeat before (flag set, with its reason) and after (flag cleared), and the "
            "`guardian_audit.jsonl` record of the re-arm."
        ),
    ),
    "removing an SL by hand": (
        (
            "On the Standard demo, with the builder's minimum-size test position open, clear its "
            "stop-loss in the terminal (Modify position, empty S/L) and wait 30 s."
        ),
        (
            "The Guardian audit record of the budget-compliant SL it placed after the grace period "
            "with its `OrderCalcProfit` loss <= L (GRD-020), and the broker read-back of the new SL."
        ),
    ),
    "tightening the daily-loss input to 0.01%": (
        (
            "Demo only: with a test position open, set the Guardian daily-loss input to 0.01% and "
            "confirm. Restore the previous value when the builder says the scenario is over."
        ),
        (
            "Guardian heartbeat with `takeover` = true and the last action, the close in the "
            "terminal's history, and the engine's T18 record (GRD-026, GRD-031)."
        ),
    ),
    "removing the EA": (
        "Remove the Guardian EA from its chart while the engine runs. Note the clock time.",
        (
            "The Guardian's final heartbeat with the deinit reason, and the engine's T9 record with a "
            "timestamp at most 20 s after the removal (GRD-012, GRD-031)."
        ),
    ),
    "disconnecting the terminal": (
        "Disconnect the computer from the network for about 60 s, then reconnect.",
        (
            "Guardian audit records of the latched kill flag and of the SL and equity re-verification "
            "after reconnect (GRD-033), and the engine's DISCONNECTED and reconnect records."
        ),
    ),
}

COVERAGE_TARGETS: tuple[tuple[str, str, str], ...] = (
    ("`src/goldbot/core/` (whole package)", ">= 95% branch", "kickoff §5 (TEST_PLAN row)"),
    ("`core/risk_engine.py`, `core/sizing.py`", "100% branch", "kickoff §5; 01 prompt M3"),
    ("`core/exposure.py`, `core/trading_state.py`", "100% branch", "01 prompt M3"),
    ("`core/money.py`, `core/convert.py`", ">= 95% branch", "01 prompt M1"),
    ("`src/goldbot/intelligence/`", ">= 95% branch", "01 prompt M6a/M6b, M6c/M6d"),
    ("Whole Python codebase", ">= 80%", "kickoff §5 (TEST_PLAN row)"),
    (
        "`sizing.py` rounding and rejection branches",
        "mutation spot check, no surviving mutants",
        "01 prompt M3",
    ),
)


class SourceError(Exception):
    """A source file cannot be parsed or holds conflicting data."""


@dataclass(frozen=True)
class Requirement:
    rid: str
    summary: str
    component: str
    test_type: str
    milestones: tuple[str, ...]
    milestone_text: str
    crit: str

    @property
    def area(self) -> str:
        if self.test_type == UNMAPPED:
            return DEFAULT_AREA
        first = self.test_type.split("+")[0].lower()
        return next((area for key, area in AREA_RULES if key in first), DEFAULT_AREA)

    @property
    def needs_mt5(self) -> bool:
        return any(key in self.test_type.lower() for key in MT5_KEYWORDS)

    @property
    def process_only(self) -> bool:
        if self.test_type == UNMAPPED:
            return False
        parts = [p.strip().lower() for p in self.test_type.split("+")]
        return all(any(re.search(m, p) for m in PROCESS_MARKERS) for p in parts)

    @property
    def test_name(self) -> str:
        if self.process_only:
            return HUMAN_TEST if HUMAN_MARKER in self.test_type.lower() else REVIEW_TEST
        rid = self.rid.lower().replace("-", "_")
        words = re.findall(r"[a-z0-9]+", self.summary.lower())[:4]
        slug = "_".join(words)[:40].rstrip("_") or "req"
        return f"tests/{self.area}/test_{rid}_{slug}.py::test_{rid}_{slug}"


def split_row(line: str) -> list[str]:
    body = line.strip()
    body = body.removeprefix("|").removesuffix("|")
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", body)]


def parse_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Return every Markdown table as (header, rows). A table starts with a header row
    followed by a separator row of dashes."""
    lines = text.split("\n")
    tables: list[tuple[list[str], list[list[str]]]] = []
    i = 0
    while i < len(lines) - 1:
        line, nxt = lines[i], lines[i + 1]
        if line.lstrip().startswith("|") and re.fullmatch(r"\s*\|[\s:|-]+\|\s*", nxt):
            header = split_row(line)
            rows: list[list[str]] = []
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            tables.append((header, rows))
        else:
            i += 1
    return tables


def milestone_sort_key(token: str) -> tuple[int, str]:
    if token == EACH:
        return (1000, "")
    if token == UNMAPPED:
        return (1001, "")
    m = re.fullmatch(r"M(\d+)([a-z]?)", token)
    if not m:
        raise SourceError(f"bad milestone token {token!r}")
    return (int(m.group(1)), m.group(2))


def parse_milestones(acceptance: str) -> tuple[tuple[str, ...], str]:
    """Milestones named in the acceptance criterion: '`test_x` passes in M4/M9; ...'."""
    m = re.search(r"passes in ([^;]+)", acceptance)
    if m:
        text = m.group(1).strip()
        tokens: set[str] = set(re.findall(r"M\d+[a-z]?", text))
        for lo, hi in re.findall(r"M(\d+)\s*[–-]\s*M(\d+)", text):
            tokens.update(f"M{n}" for n in range(int(lo), int(hi) + 1))
        if tokens:
            return tuple(sorted(tokens, key=milestone_sort_key)), text
    if re.search(r"\beach milestone\b", acceptance):
        return (EACH,), "each milestone (02 review)"
    return (UNMAPPED,), ""


def parse_requirements(text: str) -> list[Requirement]:
    tables = [t for t in parse_tables(text) if t[0] and t[0][0] == "ID"]
    if not tables:
        raise SourceError("no requirements table (header starting with 'ID') found")
    seen: dict[str, tuple[str, ...]] = {}
    reqs: dict[str, Requirement] = {}
    conflicts: list[str] = []
    for header, rows in tables:
        col = {name: idx for idx, name in enumerate(header)}

        def cell(row: list[str], name: str, col: dict[str, int] = col) -> str:
            idx = col.get(name)
            return row[idx] if idx is not None and idx < len(row) else ""

        for row in rows:
            rid = row[0]
            if not re.fullmatch(r"[A-Z]+-\d+", rid):
                raise SourceError(f"bad requirement ID {rid!r}")
            if len(row) != len(header):
                raise SourceError(f"{rid}: {len(row)} cells, header has {len(header)}")
            key = tuple(row)
            if rid in seen:
                if seen[rid] != key:
                    conflicts.append(rid)
                continue
            seen[rid] = key
            test_type = cell(row, "Verification") or UNMAPPED
            milestones, mtext = parse_milestones(cell(row, "Acceptance criterion"))
            reqs[rid] = Requirement(
                rid=rid,
                summary=cell(row, "Requirement (summary)"),
                component=cell(row, "Component"),
                test_type=test_type,
                milestones=milestones,
                milestone_text=mtext,
                crit=cell(row, "Crit."),
            )
    if conflicts:
        raise SourceError("IDs listed twice with different data: " + ", ".join(sorted(conflicts)))
    return list(reqs.values())


def parse_human_steps(text: str) -> list[str]:
    """The [HUMAN] steps listed in GUARDIAN_SAFETY_SPEC.md section 13."""
    m = re.search(r"^## 13\..*?(?=^## |\Z)", text, re.DOTALL | re.MULTILINE)
    if not m:
        raise SourceError("GUARDIAN_SAFETY_SPEC.md has no section 13")
    flat = re.sub(r"\s+", " ", m.group(0))
    m = re.search(r"In §12 these are: (.*?)\. The ", flat)
    if not m:
        raise SourceError("section 13 no longer lists the [HUMAN] steps as 'In §12 these are: ...'")
    steps = [s.strip().removeprefix("and ").strip() for s in m.group(1).split(";")]
    missing = [s for s in steps if s not in HUMAN_DETAILS]
    if missing:
        raise SourceError(f"[HUMAN] steps without instruction/evidence in HUMAN_DETAILS: {missing}")
    return steps


def esc(text: str) -> str:
    return text.replace("|", "\\|")


def render(reqs: list[Requirement], human_steps: list[str]) -> str:
    out: list[str] = []
    w = out.append
    w("# TEST_PLAN — GoldBot")
    w("")
    w("> **GENERATED FILE — do not edit by hand.** Produced by `tools/gen_test_plan.py` from")
    w("> `quality/REQUIREMENTS_TRACEABILITY.md` (columns ID, Requirement, Component, Verification,")
    w("> Acceptance criterion, Crit.) and `specifications/GUARDIAN_SAFETY_SPEC.md` §13. Change the")
    w("> sources, then run `python tools/gen_test_plan.py`. `--check` exits 1 when this file is")
    w("> stale.")
    w(">")
    w("> This is a plan. It holds no test results and moves no requirement to `VERIFIED`")
    w("> (GOV-002).")
    w(">")
    w("> Process/review-only rows (every part of `Verification` is a review, STATUS audit,")
    w("> evidence table, inspection, manual, document, CI or `[HUMAN]` marker; §2) get the test")
    w(f"> `{REVIEW_TEST}` or `{HUMAN_TEST}` instead of a pytest path, and are verified by the")
    w("> 02 review or by the human step with its evidence (`docs/DEFINITION_OF_DONE.md`).")
    w("")
    w("## 1. Coverage targets")
    w("")
    w("| Scope | Target | Source |")
    w("| --- | --- | --- |")
    for scope, target, source in COVERAGE_TARGETS:
        w(f"| {scope} | {target} | {source} |")
    w("")
    w("## 2. Mapping and naming rules")
    w("")
    w("- **Test type** = the requirement's `Verification` cell, verbatim. Empty → `UNMAPPED`.")
    w("- **Milestones** = every `M<n>[part]` token after `passes in` in the `Acceptance")
    w("  criterion` cell; a range `Mx–My` includes every milestone between. A requirement is")
    w("  listed under each milestone it names. `02 review checks it each milestone` → `EACH`.")
    w("  Nothing found → `UNMAPPED`.")
    w("- **Area** = the `tests/` folder of the M1 layout: the first rule below whose keyword")
    w("  occurs")
    w("  in the first `+`-separated part of the test type (the primary test); otherwise")
    w("  `unit`.")
    rules = ", ".join(f"`{k}` → {a}" for k, a in AREA_RULES)
    w(f"  Rules in order: {rules}.")
    w("- **Test name** = `tests/<area>/test_<id>_<slug>.py::test_<id>_<slug>`, where `<id>` is the")
    w("  requirement ID lower-cased with `-` → `_`, and `<slug>` is the first four lower-case")
    w("  alphanumeric words of the requirement summary joined by `_`, cut to 40 characters. The")
    w("  function name starts with the `test_<id>` named in the traceability acceptance")
    w("  criterion. A requirement checked by review also gets this test for its automatable part")
    w("  (scan, audit); the review itself is in `docs/DEFINITION_OF_DONE.md`.")
    marks = ", ".join(f"`{m}`" for m in PROCESS_MARKERS)
    w("- **Process/review-only** = every `+`-separated part of the test type matches one of these")
    w(f"  case-insensitive regex markers: {marks}. Such a row gets the test")
    w(f"  `{REVIEW_TEST}` (or `{HUMAN_TEST}` when the test type contains `[HUMAN]`), never a")
    w("  pytest path, because a pytest for a process rule could only be tautological. It is verified")
    w("  by the 02 review (or by the human step and its evidence). A test type with one automated")
    w("  part keeps the pytest name.")
    kws = ", ".join(f"`{k}`" for k in MT5_KEYWORDS)
    w(f"- **mt5** = `yes` when the test type mentions {kws}: at least part of the")
    w("  test needs the Windows host with the terminal (`pytest -m mt5`).")
    w("")

    by_ms: dict[str, list[Requirement]] = {}
    for r in reqs:
        for ms in r.milestones:
            by_ms.setdefault(ms, []).append(r)
    order = sorted(by_ms, key=milestone_sort_key)

    w("## 3. Totals")
    w("")
    w(f"Requirements: **{len(reqs)}** unique IDs.")
    w("")
    w("### 3.1 Per milestone")
    w("")
    w("A requirement that names several milestones counts once in each.")
    w("")
    w("| Milestone | Requirements | CRITICAL |")
    w("| --- | --- | --- |")
    for ms in order:
        rs = by_ms[ms]
        w(f"| {ms} | {len(rs)} | {sum(r.crit == 'CRITICAL' for r in rs)} |")
    w("")
    w("### 3.2 Per test type")
    w("")
    w("| Test type | Requirements |")
    w("| --- | --- |")
    for tt, n in sorted(Counter(r.test_type for r in reqs).items(), key=lambda kv: (-kv[1], kv[0])):
        w(f"| {esc(tt)} | {n} |")
    w("")
    w("### 3.3 Per area")
    w("")
    w("| Area | Requirements | of which mt5 |")
    w("| --- | --- | --- |")
    tested = [r for r in reqs if not r.process_only]
    areas = Counter(r.area for r in tested)
    for area in sorted(areas):
        n_mt5 = sum(r.needs_mt5 for r in tested if r.area == area)
        w(f"| `tests/{area}/` | {areas[area]} | {n_mt5} |")
    for label in (REVIEW_TEST, HUMAN_TEST):
        n = sum(r.test_name == label for r in reqs)
        if n:
            w(f"| {label} | {n} | |")
    w("")

    w("## 4. Requirements by milestone")
    w("")
    for ms in order:
        rs = sorted(by_ms[ms], key=lambda r: r.rid)
        title = {EACH: "EACH (checked by the 02 review in every milestone)"}.get(ms, ms)
        w(f"### {title} ({len(rs)})")
        w("")
        w("| ID | Crit. | Test type | Milestones (traceability) | mt5 | Test |")
        w("| --- | --- | --- | --- | --- | --- |")
        for r in rs:
            mt5 = "yes" if r.needs_mt5 else ""
            test = r.test_name if r.process_only else f"`{r.test_name}`"
            w(
                f"| {r.rid} | {r.crit} | {esc(r.test_type)} | {esc(r.milestone_text or UNMAPPED)} "
                f"| {mt5} | {test} |"
            )
        w("")

    w("## 5. Guardian `[HUMAN]` steps (GUARDIAN_SAFETY_SPEC §13; M2 observer and M7b)")
    w("")
    w("The builder pauses and asks the user for each step. A `[HUMAN]` test passes only with the")
    w("evidence listed (GOV-002). Step names are parsed from §13; the folder-ACL change and the")
    w("duplicate-engine test are scripted, not `[HUMAN]`.")
    w("")
    w("| # | `[HUMAN]` step (§13) | Instruction for the user | Evidence to collect |")
    w("| --- | --- | --- | --- |")
    for i, step in enumerate(human_steps, 1):
        instr, evidence = HUMAN_DETAILS[step]
        w(f"| H{i} | {esc(step)} | {esc(instr)} | {esc(evidence)} |")
    w("")

    w("## 6. UNMAPPED requirements")
    w("")
    unm = sorted(r.rid for r in reqs if r.test_type == UNMAPPED or UNMAPPED in r.milestones)
    if unm:
        w("These rows have no test type or no milestone in the traceability matrix. Fix the source")
        w("row; do not guess here.")
        w("")
        w(", ".join(unm))
    else:
        w("None: every requirement has a test type and at least one milestone.")
    w("")
    return "\n".join(out)


def build() -> tuple[str, list[Requirement]]:
    reqs = parse_requirements(TRACE.read_text(encoding="utf-8"))
    steps = parse_human_steps(GUARDIAN.read_text(encoding="utf-8"))
    return render(reqs, steps), reqs


def self_test() -> None:
    table = (
        "| ID | Requirement (summary) | Component | Verification | "
        "Acceptance criterion | Crit. |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| RISK-001 | Only the RiskEngine. More | core | Unit + property | "
        "`test_risk_001` passes in M3; evidence | CRITICAL |\n"
        "| EXE-002 | No dup | engine | FakeBroker integration + demo chaos | "
        "`test_exe_002` passes in M1–M3; e | CRITICAL |\n"
        "| GOV-001 | Read STATUS | process | Review (02 prompt) | "
        "02 review checks it each milestone; zero violations | CRITICAL |\n"
        "| UI-001 | Glass | web |  | `test_ui_001` passes in M4/M9 (theme in M6b); e |  |\n"
        "| UI-002 | X a\\|b | web | Playwright + axe | nothing here |  |\n"
        "| GOV-005 | Hand | process | [HUMAN] step + manual check | e each milestone |  |\n"
        "| SEC-001 | Keys | security | Security tests + review | `t` passes in M1; e |  |\n"
        "| RISK-001 | Only the RiskEngine. More | core | Unit + property | "
        "`test_risk_001` passes in M3; evidence | CRITICAL |\n"
    )
    reqs = {r.rid: r for r in parse_requirements(table)}
    assert list(reqs) == [
        "RISK-001", "EXE-002", "GOV-001", "UI-001", "UI-002", "GOV-005", "SEC-001"
    ], reqs
    assert reqs["GOV-001"].process_only and reqs["GOV-001"].test_name == REVIEW_TEST
    assert reqs["GOV-005"].process_only and reqs["GOV-005"].test_name == HUMAN_TEST
    assert not reqs["SEC-001"].process_only  # one automated part keeps the pytest name
    assert reqs["SEC-001"].test_name.startswith("tests/security/test_sec_001_")
    assert not reqs["UI-001"].process_only and not reqs["RISK-001"].process_only
    assert reqs["RISK-001"].milestones == ("M3",)
    assert reqs["RISK-001"].area == "unit" and not reqs["RISK-001"].needs_mt5
    assert reqs["RISK-001"].test_name == (
        "tests/unit/test_risk_001_only_the_riskengine_more.py::test_risk_001_only_the_riskengine_more"
    )
    assert reqs["EXE-002"].milestones == ("M1", "M2", "M3")
    assert reqs["EXE-002"].area == "integration" and reqs["EXE-002"].needs_mt5
    assert reqs["GOV-001"].milestones == (EACH,)
    assert reqs["UI-001"].test_type == UNMAPPED
    assert reqs["UI-001"].milestones == ("M4", "M6b", "M9")
    assert reqs["UI-002"].milestones == (UNMAPPED,)
    assert reqs["UI-002"].summary == "X a|b" and reqs["UI-002"].area == "e2e"
    conflict = table + "| EXE-002 | No dup | engine | Unit | `t` passes in M7; e | CRITICAL |\n"
    try:
        parse_requirements(conflict)
    except SourceError as exc:
        assert "EXE-002" in str(exc)
    else:
        raise AssertionError("conflicting duplicate was not rejected")
    spec = (
        "## 13. Build\n- **`[HUMAN]` steps.** Text. In §12 these are: attaching the EA and "
        "setting its inputs;\n  removing the EA; and disconnecting the terminal. The folder-ACL "
        "change is scripted.\n## 14. Next\n"
    )
    assert parse_human_steps(spec) == [
        "attaching the EA and setting its inputs",
        "removing the EA",
        "disconnecting the terminal",
    ]
    text = render(list(reqs.values()), parse_human_steps(spec))
    assert "UI-001, UI-002" in text and "\r" not in text
    assert f"| {REVIEW_TEST} |" in text and "test_gov_001" not in text
    assert text == render(list(reqs.values()), parse_human_steps(spec))
    print("self-test: OK")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--check", action="store_true", help="exit 1 if docs/TEST_PLAN.md is stale")
    ap.add_argument("--self-test", action="store_true", help="run the parser self-test")
    args = ap.parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    try:
        text, reqs = build()
    except SourceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    reviewed = sum(r.process_only for r in reqs)
    if args.check:
        current = OUT.read_bytes().decode("utf-8") if OUT.exists() else None
        if current != text:
            print(f"{OUT.relative_to(ROOT)} is out of date; run python tools/gen_test_plan.py")
            return 1
        print(
            f"{OUT.relative_to(ROOT)} is up to date ({len(reqs)} requirements, "
            f"{reviewed} review-only/HUMAN)"
        )
        return 0
    OUT.write_bytes(text.encode("utf-8"))
    unmapped = sum(r.test_type == UNMAPPED or UNMAPPED in r.milestones for r in reqs)
    print(
        f"wrote {OUT.relative_to(ROOT)}: {len(reqs)} requirements, {unmapped} UNMAPPED, "
        f"{reviewed} reclassified as review-only/HUMAN (no pytest name)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
