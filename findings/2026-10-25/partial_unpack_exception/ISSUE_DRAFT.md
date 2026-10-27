# False negative: nested unpacking loses earlier assignments in exception-handler flow

Local draft only. No issue has been filed. Duplicate search on 2026-10-25 found
no matching issue; novelty remains a best-effort assessment, not a guarantee.

## Reproduction

```python
def run(items: tuple[int, ...]) -> None:
    value: int | str = 1
    try:
        value, (a, b) = "bad", items
    except ValueError:
        print(value.bit_length())


run((1,))
```

Run with:

```bash
ty check --python-version 3.13 repro.py
```

## Actual behavior

ty 0.0.84 and 0.0.91 both report `All checks passed!` (exit 0).
Enabling `--error all` also reports no diagnostics for this program.

If `reveal_type(value)` is added inside the handler, ty reports `Literal[1]`.
However, the runtime value at that line is the string `"bad"`.

CPython 3.13.16 raises:

```text
ValueError: not enough values to unpack (expected 2, got 1)

During handling of the above exception, another exception occurred:

AttributeError: 'str' object has no attribute 'bit_length'
```

## Expected behavior

Report an error for `value.bit_length()` in the handler, or otherwise retain
the string binding when computing the handler's possible types for `value`.

The outer unpack succeeds and assigns `"bad"` to `value`. The nested unpack of
`items` into `(a, b)` then raises `ValueError`. The already-completed assignment
to `value` is not rolled back when the exception handler runs.

This follows Python's [assignment statement semantics](https://docs.python.org/3/reference/simple_stmts.html#assignment-statements):
target lists are assigned recursively, with the individual targets processed in
order. The program uses no `Any`, suppressions, unchecked callbacks, external
dependencies, or mutations through aliases. `tuple[int, ...]` legitimately has
unknown length; there is no statically invalid fixed-length unpacking here.

## Differential result

mypy 2.4.0 reports:

```text
error: Item "str" of "int | str" has no attribute "bit_length"  [union-attr]
```

This is also rejected by `mypy --strict`. Pyright 1.1.414 accepts the program,
so there is no majority-checker argument here; the runtime witness and Python's
assignment semantics establish the missed error.

## Controls

- Split the assignment into `value = "bad"` followed by `a, b = items`: ty
  correctly reports the invalid attribute access in the same exception handler.
- Put the failing nested target first, `(a, b), value = items, "bad"`: Python
  keeps the old integer value, and the handler succeeds.
- Guard the attribute access with `isinstance(value, int)`: all three checkers
  accept the program under default rules and it finishes successfully. With
  `--error all`, ty incorrectly reports this condition as always true; at runtime
  it is false for the supplied input.
- Replace tuple targets with nested list targets: the false negative remains.
- Assign `None` instead of a string, with `value: int | None`: the false
  negative remains and Python raises `AttributeError` on `None`.
- Return `value` from a function annotated `-> int` in the handler: ty accepts
  a function that returns a string; mypy reports `return-value`.
- Flat unpacking to a list subscript and chained assignment to a list
  subscript correctly retain earlier stores in ty. The failure appears
  specific to nested sequence targets.

## Related implementation and duplicate checks

[ruff#27471](https://github.com/astral-sh/ruff/pull/27471) introduced exception
checkpoints before operations that can raise; it continued
[ruff#27221](https://github.com/astral-sh/ruff/pull/27221).

In the downloaded main-branch source, `SemanticIndexBuilder::add_unpackable_assignment`
records a checkpoint before an outer list/tuple target. Visiting nested sequence
targets does not appear to record another checkpoint after earlier targets have
been stored. This is a source-based hypothesis, not a compiled patch or a bisect.

The existing exception-flow mdtest covers unpacking that fails before a later
statement assigns a variable. It does not cover a later nested target failing
after an earlier target in the same assignment has been stored.

No matching report was found in the downloaded issue titles/bodies or targeted
public GitHub searches of ty issues and Ruff PRs. ty#233 concerns `finally`
suites; this reproducer has no `finally`. ty#4293 concerns preserving a declared
dictionary type after handler assignments, which is a different mechanism.

Tested: Linux x86_64, CPython 3.13.16, ty 0.0.84 / 0.0.91, mypy 2.4.0,
pyright 1.1.414. The failure was not tested against a binary built from current
Ruff main.
