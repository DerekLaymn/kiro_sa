"""Keep a known lambda bug out of the novelty queue without hiding other bugs."""

from pathlib import Path

from typediff.discrepancy import find_discrepancies
from typediff.kb import matching_entries
from typediff.models import Diagnostic, RuntimeResult, Severity, Tool
from typediff.priors import find_priors
from typediff.state import CaseState


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "findings/2026-10-25/lambda_rebinding.py").read_text()


def matches(source):
    line = next(i for i, text in enumerate(source.splitlines(), 1) if "lambda:" in text)
    diagnostic = Diagnostic(Tool.TY, line, 24, Severity.ERROR, "unsupported-operator",
                            "Operator `+` is not supported between objects of type `int | None` and `Literal[1]`")
    state = CaseState("test", source, "3.13", {Tool.MYPY: [], Tool.TY: [diagnostic]},
                      RuntimeResult(status="success"), [], {}, {})
    discrepancy = find_discrepancies(state.diags, state.amap, state.runtime)[0]
    return {entry.id for entry in matching_entries(state, discrepancy)}


def test_known_rebound_inferred_lambda_matches():
    assert "UPSTREAM-MYPY-9658" in matches(SOURCE)


def test_no_rebinding_is_not_duplicate():
    assert "UPSTREAM-MYPY-9658" not in matches(SOURCE.replace("    value = None\n", ""))


def test_annotated_lambda_is_not_duplicate():
    assert "UPSTREAM-MYPY-9658" not in matches(SOURCE.replace("callback =", "callback: Callable[[], int] ="))


def test_unrelated_rebinding_is_not_duplicate():
    assert "UPSTREAM-MYPY-9658" not in matches(SOURCE.replace("    value = None\n", "    other = None\n"))


def test_without_narrowing_is_not_duplicate():
    assert "UPSTREAM-MYPY-9658" not in matches(SOURCE.replace("    if value is None:\n        value = 0\n", ""))


def test_other_expression_in_lambda_is_not_duplicate():
    source = SOURCE.replace("lambda: value + 1", "lambda: (value, 'bad' + 1)")
    assert "UPSTREAM-MYPY-9658" not in matches(source)


def test_variadic_limitation_is_prior_only():
    source = (ROOT / "findings/2026-10-25/variadic_callback.py").read_text()
    line = len(source.splitlines())
    diagnostic = Diagnostic(Tool.MYPY, line, 14, Severity.ERROR, "arg-type", "Argument 1 has incompatible type")
    state = CaseState("test", source, "3.13", {Tool.MYPY: [diagnostic], Tool.TY: []},
                      RuntimeResult(status="success"), [], {}, {})
    discrepancy = find_discrepancies(state.diags, state.amap, state.runtime)[0]
    assert "TY-4152" in {prior.id for prior in find_priors(source, discrepancy)}
    assert not any(entry.id == "UPSTREAM-TY-4152" for entry in matching_entries(state, discrepancy))
