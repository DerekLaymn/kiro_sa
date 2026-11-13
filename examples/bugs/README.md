# Reproducers of the 12 verified bugs

One minimal program per bug. Each file is the first code block of the issue draft in [results/bugs.md](../../results/bugs.md),
where the full text (versions, duplicate search, cause) is. All were run on the pinned tools: **mypy 2.4.0, ty 0.0.97,
pyright 1.1.414, CPython 3.13** (`typediff doctor` checks your versions). Run a file with the tool named in its file name:

```bash
ty check --python-version 3.13 examples/bugs/04_ty_eq_without_hash_is_hashable.py
mypy --python-version 3.13 --no-incremental examples/bugs/03_mypy_metaclass_reflected_operator.py
pyright --pythonversion 3.13 examples/bugs/12_pyright_closed_typeddict_before_3_15.py
python examples/bugs/04_ty_eq_without_hash_is_hashable.py        # the runtime (CPython) result
```

"Verified" means reduced, reproduced on the pinned and the newest tool version, and searched on the trackers without a
duplicate. It does not mean that a maintainer confirmed the bug. Issue states are from 2026-11-06 and may have changed.

| # | Tool | File | Issue | Expected | Actual (pinned version) |
|---|---|---|---|---|---|
| 1 | ty | [01](01_ty_nested_protocol_receiver_stack_overflow.py) | [ty#4933](https://github.com/astral-sh/ty/issues/4933), open | no crash (accept or report) | `thread has overflowed its stack`, process aborts |
| 2 | ty | [02](02_ty_alias_narrowing_loop_back_edge.py) | [ty#4934](https://github.com/astral-sh/ty/issues/4934), closed, fixed by astral-sh/ruff#30074 | error on `x + 1` (`x` can be `None` on the second iteration) | `All checks passed!`; CPython raises `TypeError` |
| 3 | mypy | [03](03_mypy_metaclass_reflected_operator.py) | [mypy#22377](https://github.com/python/mypy/issues/22377), open | `A * B` is `str` (right metaclass `__rmul__` runs first) | two errors: `A * B` inferred as `int`; CPython prints `str` |
| 4 | ty | [04](04_ty_eq_without_hash_is_hashable.py) | [ty#4941](https://github.com/astral-sh/ty/issues/4941), open | `invalid-argument-type` for `need(Plain())` and `need(Sub())` | `All checks passed!`; CPython raises `TypeError: unhashable type` |
| 5 | mypy | [05](05_mypy_typevartuple_then_paramspec_default.py) | [mypy#22375](https://github.com/python/mypy/issues/22375), open | `Foo[int, str]` is accepted (PEP 696) | `Can only replace ParamSpec ...` and the type becomes `Any` (6 errors) |
| 6 | ty | [06](06_ty_nested_unpack_except_binding.py) | [ty#4958](https://github.com/astral-sh/ty/issues/4958), open | `value` in the `except` clause is `int \| str` | reveals `Literal[1]`; CPython has `'bad'` |
| 7 | pyright | [07](07_pyright_descriptor_get_decorator_rangeerror.py) | [pyright#11984](https://github.com/microsoft/pyright/issues/11984), open | no crash | `RangeError: Maximum call stack size exceeded` |
| 8 | mypy | [08](08_mypy_overloaded_post_init_override.py) | [mypy#22385](https://github.com/python/mypy/issues/22385), open | no error | `Argument 2 of "__post_init__" is incompatible with supertype "dataclass"  [override]` |
| 9 | mypy | [09](09_mypy_reflected_comparison_priority.py) | [mypy#22386](https://github.com/python/mypy/issues/22386), open | `a < b` is `str`, `a > b` is `int` | `a < b` inferred as `int` and `a > b` as `str` (3 errors); CPython prints `'lt' 7` |
| 10 | mypy | [10](10_mypy_possibly_undefined_swallowing_with.py) | not filed | `possibly-undefined` on `return value` (run with `--enable-error-code possibly-undefined`) | no report; CPython raises `UnboundLocalError` |
| 11 | mypy | [11](11_mypy_lambda_vs_callback_protocol.py) | not filed | error for each lambda whose parameter is not named `value` | only the `def` is rejected; the lambdas pass; CPython raises `TypeError` on `sink(value=1)` |
| 12 | pyright | [12](12_pyright_closed_typeddict_before_3_15.py) | not filed | error on `closed=True` with `--pythonversion` below 3.15 | no diagnostic for `closed=True`; CPython raises `TypeError` |

Bugs 1 and 7 are stack overflows, so whether and how a machine reports them can depend on its stack size.
