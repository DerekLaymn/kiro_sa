"""Mutation operators that carry their own instruction text.

The operators of DESIGN.md section 6 (``variance_flip``, ``feature_crossover``, ...) are bare names: the generator model
reads the name and guesses. They stay bare, so every prompt that used them is unchanged byte for byte (and the file-bridge
prompt keys with it). Operators added here are described to the generator: ``mutation_spec`` returns
``{"operator": name, "instruction": text}`` for them and ``{"operator": name}`` for everything else.

Day 9 adds two operators for runtime-refutable shapes:

* ``dunder_instance_shadow``  a special method that exists only on the instance or only as an annotation. CPython looks
                              special methods up on the type, so the use raises TypeError whatever the checker says.
* ``exit_swallow_flip``       the return annotation of ``__exit__`` decides whether code after a ``with`` is reachable.
                              CPython shows which one is right by running the program.
"""

from __future__ import annotations

OPERATORS: dict[str, str] = {
    "dunder_instance_shadow": (
        "Pick one class of the previous program (or define a small one) and change how ONE special method exists on it: "
        "either an annotation-only class attribute (`__call__: Callable[[int], int]`, `__iter__: Callable[[], Iterator[int]]`, "
        "`__len__: Callable[[], int]`) with no definition, or an instance assignment in `__init__` "
        "(`self.__call__ = fn`, `self.__getitem__ = fn`), or a class-level assignment of a plain function to a dunder name "
        "inside a method. Then USE the implicit protocol on an instance: call it, iterate it, `len()`, subscript, `with`, "
        "`in`, `bool()`. CPython looks special methods up on the type, so each of those uses raises TypeError. Wrap each "
        "use in try/except TypeError, mark the line `# expect-error`, and keep one control that defines the method on the "
        "class and works. Vary the protocol (call / iter / len / getitem / enter / contains) between variants."
    ),
    "exit_swallow_flip": (
        "Write a context manager class whose `__exit__` returns `bool`, then flip its annotation between `bool`, `None`, "
        "`Literal[True]` and `Literal[False]` while the body of the method keeps returning the same value. Around it put a "
        "`with` block that raises inside (a `raise ValueError` or an operation that fails) and code AFTER the block that "
        "narrows or reveals a variable assigned inside the block (`x: int | None = None` before, `x = 1` inside, "
        "`reveal_type(x)` after). Execute the program so CPython shows whether the exception was swallowed and whether "
        "the code after the block ran. Add an `@contextmanager` generator and a `contextlib.suppress` variant of the same "
        "block as controls."
    ),
}


def mutation_spec(op: str) -> dict[str, str]:
    """The mutation dict for ``--ops``: bare for the original operators, with an instruction for the Day-9 ones."""
    op = op.strip()
    return {"operator": op, "instruction": OPERATORS[op]} if op in OPERATORS else {"operator": op}
