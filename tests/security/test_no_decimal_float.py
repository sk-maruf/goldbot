"""GV-26 / RISK-020: static ban on Decimal constructions that could take a float.

Rule, applied with `ast` to every .py file under src/goldbot:

1. A call to `Decimal(...)` (by any import alias, or as `<module>.Decimal(...)`) or to
   `<ctx>.create_decimal(...)` is allowed only with no argument, a str literal, or an int literal
   (optionally negated). Anything else (a name, an attribute, a float literal, `str(x)`, an f-string,
   `*args`) is a violation, because it may carry a float.
2. Exception: `Decimal(repr(<expr>))` is the single sanctioned MT5 boundary call and is allowed only
   in src/goldbot/core/convert.py, exactly once.
3. `Decimal.from_float(...)` and `<ctx>.create_decimal_from_float(...)` are always violations.
"""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "goldbot"
SANCTIONED_FILE = SRC / "core" / "convert.py"
BANNED_ATTRS = {"from_float", "create_decimal_from_float"}


def _decimal_aliases(tree: ast.Module) -> tuple[set[str], set[str]]:
    """Names bound to decimal.Decimal, and names bound to the decimal module."""
    names: set[str] = set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "decimal":
            names |= {
                "Decimal" if a.name == "*" else a.asname or a.name
                for a in node.names
                if a.name in ("Decimal", "*")
            }
        elif isinstance(node, ast.Import):
            modules |= {a.asname or a.name for a in node.names if a.name == "decimal"}
    return names, modules


def _is_safe_literal(arg: ast.expr) -> bool:
    if isinstance(arg, ast.UnaryOp) and isinstance(arg.op, ast.USub):
        arg = arg.operand
    return isinstance(arg, ast.Constant) and (
        isinstance(arg.value, str) or (isinstance(arg.value, int) and not isinstance(arg.value, bool))
    )


def _is_repr_call(arg: ast.expr) -> bool:
    return isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id == "repr"


def scan(source: str, filename: str, *, sanctioned: bool = False) -> tuple[list[str], int]:
    """Return (violations, number of sanctioned `Decimal(repr(...))` calls)."""
    tree = ast.parse(source, filename)
    names, modules = _decimal_aliases(tree)
    violations: list[str] = []
    repr_sites = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        where = f"{filename}:{node.lineno}"
        if isinstance(func, ast.Attribute) and func.attr in BANNED_ATTRS:
            violations.append(f"{where}: {func.attr}() is banned")
            continue
        is_ctor = (isinstance(func, ast.Name) and func.id in names) or (
            isinstance(func, ast.Attribute)
            and (
                func.attr == "create_decimal"
                or (func.attr == "Decimal" and isinstance(func.value, ast.Name) and func.value.id in modules)
            )
        )
        if not is_ctor:
            continue
        value = (
            node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == "value"), None)
        )
        if any(isinstance(a, ast.Starred) for a in node.args) or any(k.arg is None for k in node.keywords):
            violations.append(f"{where}: Decimal(*args/**kwargs) may carry a float")
        elif value is None or _is_safe_literal(value):
            pass
        elif sanctioned and _is_repr_call(value):
            repr_sites += 1
        else:
            violations.append(f"{where}: Decimal({ast.unparse(value)}) may carry a float; use to_decimal()")
    return violations, repr_sites


def _src_files() -> list[Path]:
    return sorted(SRC.rglob("*.py"))


def test_gv26_no_decimal_float_construction_in_src() -> None:
    violations: list[str] = []
    for path in _src_files():
        found, _ = scan(path.read_text(encoding="utf-8"), str(path), sanctioned=path == SANCTIONED_FILE)
        violations += found
    assert violations == []


def test_gv26_convert_has_exactly_one_sanctioned_repr_site() -> None:
    _, sites = scan(SANCTIONED_FILE.read_text(encoding="utf-8"), str(SANCTIONED_FILE), sanctioned=True)
    assert sites == 1


# --- scanner self-test: planted snippets (parsed inline, never written into src) ----------------

BAD = [
    "from decimal import Decimal\nDecimal(1.1)",
    "from decimal import Decimal\nDecimal(-1.5)",
    "from decimal import Decimal\nx = 1.0\nDecimal(x)",
    "from decimal import Decimal\nDecimal(tick.bid)",
    "from decimal import Decimal\nDecimal(str(x))",
    "from decimal import Decimal\nDecimal(f'{x}')",
    "from decimal import Decimal\nDecimal(repr(x))",  # repr outside convert.py
    "from decimal import Decimal\nDecimal(*args)",
    "from decimal import Decimal\nDecimal(value=x)",
    "from decimal import Decimal\nDecimal(**kw)",
    "from decimal import Decimal as D\nD(x)",
    "import decimal\ndecimal.Decimal(x)",
    "import decimal as dm\ndm.Decimal(0.5)",
    "from decimal import Decimal\nDecimal.from_float(x)",
    "ctx.create_decimal(x)",
    "ctx.create_decimal_from_float(x)",
    "from decimal import Decimal\nDecimal(True)",
]

GOOD = [
    "from decimal import Decimal\nDecimal('1.10')",
    "from decimal import Decimal\nDecimal(1)",
    "from decimal import Decimal\nDecimal(-1)",
    "from decimal import Decimal\nDecimal()",
    "from decimal import Decimal\nDecimal(value='0.01')",
    "from decimal import Decimal as D\nD('0.01')",
    "import decimal\ndecimal.Decimal('2')",
    "ctx.create_decimal('1.5')",
    "Decimal(x)",  # not decimal.Decimal: no import binds the name
    "other.Decimal(x)",  # attribute on a non-decimal module
]


@pytest.mark.parametrize("snippet", BAD)
def test_scanner_flags_planted_bad_snippet(snippet: str) -> None:
    violations, _ = scan(snippet, "<planted>")
    assert violations, snippet


@pytest.mark.parametrize("snippet", GOOD)
def test_scanner_accepts_safe_snippet(snippet: str) -> None:
    violations, _ = scan(snippet, "<planted>")
    assert violations == [], snippet


def test_scanner_counts_repr_site_only_when_sanctioned() -> None:
    snippet = "from decimal import Decimal\nDecimal(repr(x))"
    assert scan(snippet, "<planted>", sanctioned=True) == ([], 1)
