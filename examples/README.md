# Examples

| Path | Content |
|---|---|
| [bugs/](bugs/README.md) | One minimal reproducer for each of the 12 verified bugs, with the expected and the actual output and the upstream issue. |
| `known_divergences.py` | Six discrepancies that the KB closes deterministically (redeclaration, `Callable.__name__`, join versus union, literal widening, assignment narrowing, and an error cascade). |
| `needs_experiments.py` | A `==`-narrowing difference that is dismissed only after a config-toggle experiment confirms it, and a mutable-override case that goes to review. |
| `self_param_unsound.py` | The case that shaped the `Self` rules: reported as ty#4656 and closed as intended behaviour. Explained in [docs/design.md](../docs/design.md#8-worked-example-the-case-that-taught-these-rules-real-ty-0084). |
| [ajay_examples/](ajay_examples/README.md) | 40 standalone programs, each probing a different part of ty's type system, with a table of the first findings. |
| [replay/](replay/README.md) | 250 stored model answers and the parent programs of the last generation round, for replay without an LLM. |

Run a walkthrough file with the judge:

```bash
typediff --python-version 3.13 run examples/known_divergences.py --keep-names
```

Expected results of the three walkthrough files on ty 0.0.84 / mypy 2.4.0 are described in [docs/design.md](../docs/design.md).
