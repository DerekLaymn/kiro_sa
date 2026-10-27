# Differential bug investigation — 2026-10-25

Follow-up: the findings below are already known or potentially covered upstream.
The subsequent search for a new report is recorded in
[partial_unpack_exception/README.md](partial_unpack_exception/README.md), with a
new generated seed, controls, duplicate-search audit, and local issue draft.
An independent subsequent mypy candidate is documented in
[overloaded_post_init/README.md](overloaded_post_init/README.md).

Repository baseline: `0e2b90c5853c46d6703ef74da0d465a701c33513` (main, pulled before investigation).
All changes and evidence are local. No GitHub issue, comment, commit, or push was made.

Two existing example leads were reduced to executable, 12-line reproducers and
validated using the pipeline, three checkers, direct CPython execution, and controls.
These are reproducible false negatives, with upstream novelty qualified below.

## 1. ty accepts invalid calls through a variadic callback wrapper

Reproducer: [variadic_callback.py](variadic_callback.py).
Reduced from `examples/ajay_examples/01_typevartuple_shapes.py`.

```python
from collections.abc import Callable

def invoke[*Ts, R](fn: Callable[[*Ts], R], *args: *Ts) -> R:
    return fn(*args)

def increment(value: int) -> int:
    return value + 1

print(invoke(increment, "bad"))
```

- **Actual:** ty 0.0.84 and 0.0.91 accept the entire program without diagnostics.
- **Expected:** reject the call: `increment` requires one integer argument.
- **mypy 2.4.0:** rejects it with `arg-type`, including under `--strict`.
- **pyright 1.1.414:** rejects it with `reportArgumentType`.
- **CPython 3.13.16:** raises `TypeError: can only concatenate str (not "int") to str`.
- **Classification:** ty false negative; reproducible runtime unsoundness.

There is no `Any`, suppression, third-party import, invalid function body, or
mutation in this reproducer. A solution for `Ts` must satisfy both the callback
signature and the forwarded arguments. For `increment`, accepting the string
would require accepting it as an integer argument.

The [typing specification's Callable/TypeVarTuple section](https://typing.python.org/en/latest/spec/generics.html#type-variable-tuples-with-callable)
uses the same relationship between a callable's parameter types and a supplied
tuple, and marks mismatched argument types as errors. Our tuple-argument control
is rejected by ty, while the `*args` form is accepted.

Controls and mutations, with identical outcomes on both tested ty versions:

| Case | mypy | ty | pyright | Direct Python |
|---|---|---|---|---|
| Variadic wrapper, string instead of integer | reject | **accept** | reject | TypeError |
| Variadic wrapper, correct integer | accept | accept | accept | prints 2 |
| Variadic wrapper, extra argument | reject | **accept** | reject | TypeError |
| Variadic wrapper, missing argument | reject | **accept** | reject | TypeError |
| Direct call with string | reject | reject | reject | TypeError |
| Same forwarding using ParamSpec | reject | reject | reject | TypeError |
| Same relationship using `args: tuple[*Ts]` | reject | reject | reject | TypeError |
| Legacy TypeVarTuple/Unpack syntax, string argument | reject | **accept** | reject | TypeError |

**Upstream status:** do not claim this is a new root cause. Searches of issue
titles and bodies found related open tracking issues:

- [ty#4152](https://github.com/astral-sh/ty/issues/4152), TypeVarTuple constraint-set support.
- [ty#4262](https://github.com/astral-sh/ty/issues/4262), fixed-length inference in nested callable parameters.

The #4262 reproducer has an additional nested callable; this one directly calls
the provided callback and demonstrates wrong type and arity at runtime. The
relationship to #4152 could be the same implementation limitation. No claim of
an independent root cause has been established. This is suitable as an additional
reproducer for discussion on those existing issues, subject to human review.

## 2. mypy retains invalid narrowing in an inferred lambda

Reproducer: [lambda_rebinding.py](lambda_rebinding.py).
Reduced from `examples/ajay_examples/30_closures_nonlocal.py`.

`build` first makes `value` an integer, creates `lambda: value + 1`, then assigns
`None` to the captured variable and returns the lambda. Calling it must read the
new value from the closure.

- **mypy 2.4.0:** accepts it, including under `--strict`.
- **ty 0.0.84 and 0.0.91:** reject the addition with `unsupported-operator`.
- **pyright 1.1.414:** rejects it with `reportOptionalOperand`.
- **CPython 3.13.16:** raises `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`.
- **Classification:** mypy false negative, **known upstream bug**.

The explicit `callback: Callable[[], int]` annotation makes mypy report the error.
Replacing the lambda with a nested, annotated `def` also makes mypy report it.
Removing the later assignment makes all three checkers accept the program and
Python print 2. This isolates the failure to inferred lambda closure narrowing.

**Duplicate check:** [mypy#9658](https://github.com/python/mypy/issues/9658)
describes this exact behavior and was open when checked. Also related:
[mypy#10993](https://github.com/python/mypy/issues/10993). Do not file a new issue.
Mypy's own [closure narrowing documentation](https://mypy.readthedocs.io/en/stable/common_issues.html#narrowing-and-inner-functions)
explains why later reassignment must be considered.

## Evidence and replay

`verify.py` generates all 12 cases above (8 variadic cases and 4 closure cases),
runs isolated mypy/ty/pyright checks, repeats mypy with `--strict`, and runs each
program directly under CPython. It records the versions, flags, stdout, stderr,
and exit codes in JSON. Direct runtime execution does not use the harness.

Current-version replay from the repository root:

```bash
uv venv --python 3.13 /tmp/typediff-current
uv pip install --python /tmp/typediff-current/bin/python \
  ty==0.0.91 mypy==2.4.0 pyright==1.1.414 typing_extensions==4.16.0 pytest==9.1.1
PYTHONPATH=. /tmp/typediff-current/bin/python findings/2026-10-25/verify.py \
  --out runs/bughunt/current-matrix
PYTHONPATH=. /tmp/typediff-current/bin/python -m typediff.cli \
  --llm null --python-version 3.13 --no-reduce --out runs/bughunt/replay \
  run findings/2026-10-25/variadic_callback.py \
      findings/2026-10-25/lambda_rebinding.py --keep-names
```

Saved evidence:

- `evidence/current-matrix.json`: direct verification with ty 0.0.91.
- `evidence/pinned-matrix.json`: direct verification with ty 0.0.84.
- `evidence/current/`: pipeline reports with ty 0.0.91.
- `evidence/pinned/`: pipeline reports with ty 0.0.84.

The pipeline preserves both findings at **REVIEW**, with verified strong runtime
evidence and weak pyright consensus. No LLM was configured, so it does not issue
an automatic CONFIRMED verdict. The false-negative classifications above are
manual assessments supported by the executable reproducers and controls; the
pipeline's stored verdicts have not been changed.

The existing regression suite passed: **58 tests**, using Python 3.13.16,
mypy 2.4.0, ty 0.0.91, pyright 1.1.414, and pytest 9.1.1. The checker tools were
found next to that interpreter, so tool-dependent tests ran rather than skipped.
No pipeline implementation change was needed to expose these disagreements.
