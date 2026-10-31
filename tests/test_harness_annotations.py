"""Pipeline defect (kb-loop round 1): the runtime harness leaked its own `from __future__ import annotations` into the
program, so CPython 'succeeded' on unquoted forward references that really raise NameError on 3.13."""

from __future__ import annotations

from typediff.runners import Runners, ToolConfig


def run(src):
    return Runners(ToolConfig(python_version="3.13")).run_runtime(src)


def test_unquoted_forward_reference_raises_nameerror():
    r = run("class C:\n    def f(self, x: C) -> None: ...\n")
    assert r.status == "exception" and r.exc_type == "NameError"


def test_program_with_its_own_future_import_still_succeeds():  # negative
    r = run("from __future__ import annotations\n\n\nclass C:\n    def f(self, x: C) -> None: ...\n")
    assert r.status == "success"


def test_quoted_forward_reference_succeeds():  # negative
    r = run("class C:\n    def f(self, x: 'C') -> None: ...\n")
    assert r.status == "success"
