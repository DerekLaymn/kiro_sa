# False-positive override error for an overloaded dataclass __post_init__

Local draft; not posted. Public issue searches performed before the offline-only
request found no matching report. This is a candidate new report, with novelty
limited by the search coverage documented in `evidence/novelty-audit.json`.

## Reproduction

```python
from dataclasses import InitVar, dataclass
from typing import overload


@dataclass
class Record:
    value: InitVar[int]

    @overload
    def __post_init__(self, value: int) -> None: ...
    @overload
    def __post_init__(self, value: str) -> None: ...
    def __post_init__(self, value: int | str) -> None:
        print(value)


Record(1)
```

Check with `mypy --python-version 3.13 --no-incremental repro.py`.

## Actual behavior

mypy 2.4.0 rejects the string overload, including under `--strict`:

```text
error: Argument 2 of "__post_init__" is incompatible with supertype "dataclass";
supertype defines the argument type as "int"  [override]
```

ty 0.0.84, ty 0.0.91, and pyright 1.1.414 accept the program. CPython 3.13.16
prints `1` and exits successfully.

## Expected behavior

Accept the overload set. The generated initializer passes an integer to
`self.__post_init__`, and the integer overload accepts that argument. The
additional string overload does not remove support for the generated call;
the implementation accepts both declared types and returns `None`.

The [typing specification's callable assignability rule](https://typing.python.org/en/latest/spec/callables.html#overloads)
allows an overloaded callable to satisfy a non-overloaded callable when one
of its signatures is compatible. Python's [dataclass post-init rules](https://docs.python.org/3/library/dataclasses.html#post-init-processing)
define which InitVar arguments are passed by the generated initializer.

Thus a hook with `(value: int) -> None` and `(value: str) -> None` overloads
satisfies the generated `(value: int) -> None` call. Successful execution and
checker consensus are supporting evidence; the assignability rule is the
reason this rejection is incorrect.

## Controls

- Remove the overload declarations and retain the implementation accepting
  `int | str`: all three checkers accept it.
- Use a single hook accepting `int`: all three checkers accept it.
- Reverse the overload order: mypy still rejects the string overload.
- Use the same overload set for an ordinary method overriding a base method
  that accepts `int`: mypy accepts it.
- Assign the bound hook to `Callable[[int], None]`: mypy reports no assignment
  error, while retaining the error on the string overload declaration.
- Use a second overload with an extra required argument rather than a string:
  mypy again rejects the extra overload, although the first overload supports
  the generated call and the program runs successfully.
- Make the InitVar keyword-only or give it a default: the false positive remains.
- Remove every integer-compatible hook overload: mypy and ty both reject this
  invalid control, and Python raises an `AttributeError` in its hook body.
- Supply a string to the integer constructor parameter: all three checkers
  reject that separate invalid call.

## Source inspection

In the installed 2.4.0 sources, `check_func_item` in `mypy/checker.py` invokes
the dataclass plugin's `check_post_init` for individual function items. The
plugin compares `defn.type` with the synthesized ideal hook signature using
`check_override`. This appears to validate each overload independently instead
of validating the combined overloaded callable. The downloaded master sources
retain the same call and comparison. This is a source-based explanation; no
patched checker or binary built from master was used for this report.

[mypy#15503](https://github.com/python/mypy/pull/15503) introduced the general
hook signature validation, closing #15498 and #9254. Those reports concern
invalid hook signatures and inheritance, not rejection of a compatible overload
set. No matching issue or PR was found in the downloaded searches.

Environment: Linux x86_64, CPython 3.13.16, mypy 2.4.0, ty 0.0.84 / 0.0.91,
pyright 1.1.414. The source and tests use only the standard library.
