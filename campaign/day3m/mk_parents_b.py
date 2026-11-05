"""Promote parents found in the Day-2 replay triage (Plan section 3 morning, promote, sources b/d).

'verbatim' entries copy the program from the replay report (checker/crash behaviour depends on exact text);
'trimmed' entries are hand-reduced to the construct that produced the strong evidence and keep a runtime witness.
"""
import json
from pathlib import Path

R = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa")
H = R / "runs" / "hits"
RUN = R / "runs" / "day3" / "replay"


def verbatim(seed_id):
    src = json.loads((RUN / f"{seed_id}.json").read_text())["source"]
    lines = src.split("\n")
    while lines and (lines[0].startswith("# area:") or lines[0].startswith("# origin:")):
        lines.pop(0)
    return "\n".join(lines)


items = [
    ("d3p_crash_ty_stack_overflow_protocol_flatten", "async_generators",
     "ty aborts with a stack overflow on a PEP 695 protocol whose method takes `self: Stream[Stream[T]]`, used through @asynccontextmanager. Vary: drop the decorator, make the protocol covariant, use a plain generic class, nest Stream three deep.",
     "runs/day2/out3 seed-50a85e2bdd8d (ruff mdtest with/async.md block 43; live ty crash, no upstream entry matched)",
     verbatim("seed-50a85e2bdd8d")),
    ("d3p_crash_mypy_segv_recursive_tvt_default_alias", "recursive_aliases",
     "mypy segfaults on PEP 695 aliases whose TypeVarTuple default is the alias itself (type Nested[*Ts = Nested[*Ts]]). Vary: ParamSpec or TypeVar default instead of TypeVarTuple, a list instead of a tuple, mutual recursion between two aliases.",
     "runs/day2/out3 seed-918936c5da72 (ruff mdtest generics/pep695/aliases.md block 17; live mypy SIGSEGV, narrow upstream matcher did not apply)",
     verbatim("seed-918936c5da72")),
    ("d3p_crash_ty_panic_partial_or_none_in_loop", "callables",
     "ty panics inside salsa when a loop repeatedly widens `value = value | None` on a functools.partial or staticmethod object. Vary: other callable wrappers (classmethod, property), a for loop instead of while, `None | value`, a lambda.",
     "runs/day2/out3 seed-dc88d8cc6015 (ruff mdtest annotations/union.md block 11; live ty panic)",
     verbatim("seed-dc88d8cc6015")),
    ("d3p_crash_ty_timeout_typeis_generic_in_loop", "narrowing_user",
     "ty times out (120 s) on a loop that reassigns `value` from a generic TypeIs guard whose argument is type(value). Vary: TypeGuard instead of TypeIs, drop the generic, bound the loop with for, use a non-type argument.",
     "runs/day2/out3 seed-23cf4835dc66 (ruff mdtest narrow/type_guards.md block 49; live ty timeout)",
     verbatim("seed-23cf4835dc66")),
    ("d3p_callables_partial_too_many_positional", "callables",
     "functools.partial(f, 1, 2, 3) binds more positional arguments than f accepts; CPython raises when the partial is called, mypy is silent and ty flags only the partial() line. Vary: keyword arguments, a method, a Protocol-typed callable, a ParamSpec decorator that returns partial.",
     "runs/day2/out3 seed-67774769f97e (ruff mdtest call/functools_partial.md block 23; runtime_miss, mypy silent)",
     verbatim("seed-67774769f97e")),
    ("d3p_inheritance_mro_hash_none_from_eq", "inheritance_mro",
     "A class that defines __eq__ but not __hash__ gets __hash__ = None at runtime; calling it raises TypeError and only pyright reports it (mypy and ty are silent). Vary: dataclass(eq=True), a subclass that restores __hash__, a set or dict-key use, a Hashable protocol argument.",
     "runs/day2/out3 seed-67975a0c41c4 (pyright tests/samples/hashability3.py; runtime_miss, mypy and ty silent)",
     "class A: ...\n\n\nA().__hash__()\n\n\nclass B:\n    def __eq__(self, value: object) -> bool:\n        return True\n\n\nB().__hash__()\n"),
    ("d3p_typevartuple_unpack_paramspec_default_after_tvt", "typevartuple_unpack",
     "Generic[*Ts, P] with a defaulted ParamSpec after a TypeVarTuple raises TypeError at runtime in 3.13, while ty and mypy accept it and disagree on every reveal. Vary: a defaulted TypeVar after *Ts, PEP 695 class Callback[*Ts, **P = [bool]], P before *Ts.",
     "runs/day2/out3 seed-570818101ed2 (ruff mdtest generics/legacy/typevartuple.md block 30; runtime_miss + reveal mismatches)",
     verbatim("seed-570818101ed2")),
    ("d3p_constructors_metaclasses_type_call_generic_base", "constructors_metaclasses",
     "type(name, (Container[int],), {}) fails at runtime (MRO entry resolution needs types.new_class) while ty reveals the class precisely and mypy reveals Any. Vary: types.new_class instead of type(), a non-generic alias base, two conflicting specialisations.",
     "runs/day2/out3 seed-badf7d3532a5 (ruff mdtest call/type.md block 28; runtime_miss + only_ty)",
     verbatim("seed-badf7d3532a5")),
    ("d3p_constructors_metaclasses_missing_kwonly_class_args", "constructors_metaclasses",
     "A metaclass __new__ with required keyword-only parameters: a class statement that omits them raises TypeError at runtime; only pyright reports the missing arguments (mypy and ty are silent). Vary: **kwargs, a default value, __init_subclass__ instead of a metaclass, a wrong keyword type.",
     "runs/day2/out3 seed-1cadfac7cbe5 (pyright tests/samples/metaclass9.py; runtime_miss, trimmed to the construct)",
     "from typing import Any\n\n\nclass Meta1(type):\n    def __new__(mcs, name: str, bases: tuple[type, ...], attrs: dict[str, Any], *, param1: int, param2: str) -> \"Meta1\":\n        return super().__new__(mcs, name, bases, attrs)\n\n    def __init__(cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any], *, param1: int, param2: str) -> None:\n        super().__init__(name, bases, attrs)\n\n\nclass Class1_1(metaclass=Meta1, param1=1, param2=\"\"): ...\n\n\nclass Class1_4(metaclass=Meta1): ...  # runtime: TypeError, missing keyword-only arguments\n"),
    ("d3p_enums_literals_intenum_true_aliases_one", "enums_literals",
     "In an IntEnum, `TRUE = True` after `ONE = 1` is an alias of ONE at runtime (Integer.TRUE is Integer.ONE, value 1); mypy and pyright keep TRUE as a separate member with value Literal[True], ty collapses it. Vary: auto() and an explicit duplicate value, StrEnum duplicates, Flag aliases, `1.0` as a value.",
     "runs/day2/out3 seed-0aa2461b8e0e (ruff mdtest enums.md block 1; reveal mismatch contradicted by runtime value)",
     "from enum import IntEnum\nfrom typing import reveal_type\n\n\nclass Integer(IntEnum):\n    ONE = 1\n    TRUE = True\n    TWO = 2\n\n\nreveal_type(Integer.TRUE.value)\nreveal_type(Integer.TRUE)\nprint(Integer.TRUE is Integer.ONE, repr(Integer.TRUE.value))\n"),
    ("d3p_inheritance_mro_total_ordering_inherited_lt", "inheritance_mro",
     "With @functools.total_ordering, __lt__ is inherited from Base and __gt__ is defined locally; mypy reveals the opposite literal for `c1 < c2` and `c1 > c2` than ty and pyright, and Any for the synthesized methods. Vary: define __le__ locally, swap which base supplies the ordering method, return bool instead of Literal.",
     "runs/day2/out3 seed-bcd8afd96f79 (ruff mdtest decorators/total_ordering.md block 8; reveal mismatch, mypy contradicts runtime)",
     "from functools import total_ordering\nfrom typing import Literal, reveal_type\n\n\nclass Base:\n    def __lt__(self, other: \"Base\") -> Literal[True]:\n        return True\n\n\n@total_ordering\nclass Child(Base):\n    def __gt__(self, other: \"Child\") -> Literal[False]:\n        return False\n\n\nc1 = Child()\nc2 = Child()\nreveal_type(c1 < c2)\nreveal_type(c1 > c2)\nreveal_type(c1 <= c2)\nprint(c1 < c2, c1 > c2, c1 <= c2, c1 >= c2)\n"),
    ("d3p_constructors_metaclasses_reflected_operator_on_metaclass", "constructors_metaclasses",
     "A + B where B's metaclass subclasses A's metaclass and overrides __radd__: CPython tries the reflected method first and returns 'right'; mypy and pyright reveal 'left', ty reveals 'right'. Vary: a different operator, the override on the instance level instead of the metaclass, a non-subclass metaclass pair.",
     "runs/day2/out3 seed-d68de70a95aa (ruff mdtest binary/instances.md block 9; reveal mismatch contradicted by runtime)",
     "from typing import Literal, reveal_type\n\n\nclass LeftMeta(type):\n    def __add__(cls, other: object) -> Literal[\"left\"]:\n        return \"left\"\n\n\nclass RightMeta(LeftMeta):\n    def __radd__(cls, other: object) -> Literal[\"right\"]:\n        return \"right\"\n\n\nclass A(metaclass=LeftMeta): ...\n\n\nclass B(metaclass=RightMeta): ...\n\n\nreveal_type(A + B)\nprint(A + B)\n"),
    ("d3p_narrowing_user_attr_narrowing_kept_after_method_call", "narrowing_user",
     "ty keeps the narrowed Literal['a'] for a.x in a class body and in a comprehension after a.update_x('b') changed it (the mdtest marks this TODO); mypy reveals str | None, runtime value is 'b'. Vary: a function body, a lambda, a property setter, the mutation through an alias or a list element.",
     "runs/day2/out3 seed-a9f445b3a193 (ruff mdtest narrow/conditionals/nested.md block 4; reveal mismatch contradicted by runtime)",
     "from typing import reveal_type\n\n\nclass A:\n    x: str | None = None\n\n    def update_x(self, value: str | None) -> None:\n        self.x = value\n\n\na = A()\na.x = \"a\"\na.update_x(\"b\")\n\n\nclass D:\n    reveal_type(a.x)\n    print(a.x)\n\n\nreveal_type([a.x for _ in range(1)])\nprint([a.x for _ in range(1)])\n"),
]
for name, area, hyp, origin, body in items:
    (H / f"{name}.py").write_text(f"# area: {area}\n# hypothesis: {hyp}\n# origin: {origin}\n{body.rstrip()}\n")
print(len(items), "written")
