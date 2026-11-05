"""Build runs/hits parents from the team's filed/known reproducers (Plan section 3 morning, promote).

Header (area/hypothesis/origin) + verbatim body of each reproducer.
"""
import subprocess
from pathlib import Path

P = Path("/home/derek/Projects/5th_sem/Software_analysis/project")
R = P / "kiro_sa"
H = R / "runs" / "hits"
BR = "fuzz/llm-run-2026-10-27"
FD = "findings/2026-10-27-llm-run/"


def git(path):
    return subprocess.run(["git", "-C", str(R), "show", f"{BR}:{FD}{path}"], capture_output=True, text=True, check=True).stdout


def strip_leading_comments(src):
    lines = src.split("\n")
    i = 0
    while i < len(lines) and lines[i].startswith("#"):
        i += 1
    return "\n".join(lines[i:])


XV = P / "temp/xfer/var"
CR = R / ".agents/tasks/crash25-repros"
ML = R / "calibration/must_stay_live"

items = [
    ("d3p_callables_self_call_attr", "callables",
     "A class whose __call__ is only an attribute annotated with the class itself; checkers recurse or disagree when the instance is called. Vary: __call__ typed as a Callable alias, a Union with None, a property, or a base-class annotation.",
     "project/temp/xfer/var/A1.py (team-filed minimized repro)", (XV / "A1.py").read_text()),
    ("d3p_self_classmethods_self_call_union", "self_classmethods",
     "`__call__: Self | None` on a class and a call on an instance; resolving a Self-typed __call__ attribute segfaults mypy and overflows ty's stack, and CPython raises TypeError (None is not callable). Vary: Self in a tuple, Optional[Self], a classmethod __call__, a subclass instance.",
     "project/temp/xfer/var/A5.py (team-filed minimized repro; bound to a real instance so CPython runs the call: A5 itself stops at NameError, mypy still segfaults and ty still overflows its stack on this form)",
     "from typing import Self\n\n\nclass C:\n    __call__: Self | None = None\n\n\nx: C = C()\nx()\n"),
    ("d3p_descriptors_decorated_get", "descriptors_properties",
     "A decorator defined in the class body (no self) applied to __get__, then __get__ accessed on the class; descriptor lookup through a decorated dunder disagrees between checkers. Vary: decorate __set__, use a staticmethod/classmethod decorator, or return a descriptor from the decorator.",
     "project/temp/xfer/var/A7.py (team-filed minimized repro)", (XV / "A7.py").read_text()),
    ("d3p_generics_contravariant_recursive_base", "generics_variance",
     "A contravariant generic whose subclass uses itself inside its own base (class C(N[N['C']])) and is assigned to N[C]; subtype checking recurses. Vary: covariant/invariant parameter, add a type parameter to C, return instead of assign.",
     "project/temp/xfer/var/B1.py (team-filed minimized repro; B4 is the same with a return)", (XV / "B1.py").read_text()),
    ("d3p_generics_contravariant_recursive_generic_base", "generics_variance",
     "Generic variant of the recursive contravariant base: class C(Generic[X], N[N['C[C[X]]']]) assigned to N[C[int]]; expanding the base grows the type without bound. Vary: nesting depth in the base string, covariance, a second type parameter.",
     "project/temp/xfer/var/D7.py (team-filed minimized repro; D10 is the same with a return)", (XV / "D7.py").read_text()),
    ("d3p_paramspec_identity_applied_to_itself", "paramspec_concatenate",
     "A ParamSpec identity decorator applied to itself (id(id)); solving P and R against a generic callable argument loops or crashes. Vary: use Concatenate, apply a decorator to a decorator that adds an argument, nest three levels.",
     "project/temp/xfer/var/C1.py (team-filed minimized repro; C3 is the TypeVar/ParamSpec spelling)", (XV / "C1.py").read_text()),
    ("d3p_paramspec_self_annotated_dunder_call", "paramspec_concatenate",
     "`self` annotated as Callable[P, T] in __init__ and __call__ with P.args/P.kwargs after a positional parameter; the checker mishandles a self type that is a ParamSpec callable. Vary: make __call__ a classmethod (E6), drop the extra x: int, annotate self with Concatenate.",
     "project/temp/xfer/var/E8.py (team-filed minimized repro; E6 is the classmethod form)", (XV / "E8.py").read_text()),
    ("d3p_generics_callable_attr_contravariant", "generics_variance",
     "A PEP 695 generic class stores a Callable[[T], None]; mypy accepts Handler[float] where Handler[int] is expected and the call fails at runtime. Vary: store the callback in a list/dict/tuple, use a property setter, use a Protocol with __call__, change the parameter to Callable[[T], T].",
     "project/temp/mypy_callable_variance.py (team-filed mypy variance report)", (P / "temp/mypy_callable_variance.py").read_text()),
    ("d3p_protocols_generic_protocol_stack_overflow", "protocols",
     "Two generic protocols whose method takes the other protocol specialised with a method-level TypeVar (P1[T2] | P2[T2]); ty overflows the stack while comparing them. Vary: add a third protocol, make T1 contravariant, change the union to a single protocol.",
     "kiro_sa/.agents/tasks/crash25-repros/ty_TB_protocol_stack_overflow.py (ty crash)", (CR / "ty_TB_protocol_stack_overflow.py").read_text()),
    ("d3p_recursive_aliases_type_of_self_alias", "recursive_aliases",
     "A generic alias Meta[T] = type[T] used recursively as `type X = Meta[X]`; mypy segfaults while expanding it. Vary: use list[T] or Callable[[T], T] instead of type[T], add a second alias, make the alias generic in X.",
     "kiro_sa/.agents/tasks/crash25-repros/mypy_A_typealias_segfault.py (mypy crash)", (CR / "mypy_A_typealias_segfault.py").read_text()),
    ("d3p_generics_typevar_default_refers_to_itself", "generics_variance",
     "A TypeVar whose default is a string naming itself, used as a Generic parameter; mypy crashes on the cyclic default. Vary: the default names another TypeVar, use PEP 695 `class C[T = T]`, use ParamSpec/TypeVarTuple defaults.",
     "kiro_sa/.agents/tasks/crash25-repros/mypy_E_typevar_default_self.py (mypy crash)", (CR / "mypy_E_typevar_default_self.py").read_text()),
    ("d3p_narrowing_user_index_assign_stale", "narrowing_user",
     "After narrowing xs[0] is not None and then assigning xs[0] = None, mypy keeps the stale narrowed int and misses the runtime TypeError. Vary: dict key, nested index xs[0][1], attribute of a subscript, a method call between narrowing and use, a negative or variable index.",
     "fuzz/llm-run-2026-10-27 bug-01 (mypy stale index narrowing, candidate)",
     strip_leading_comments(git("bug-01-narrowing-mypy-stale-index-narrowing.py"))),
    ("d3p_enums_flag_or_literal_union", "enums_literals",
     "ty infers Literal[F.R, F.W] for F.R | F.W on an enum.Flag although the runtime value is neither member (spec exempts Flag from literal expansion). Vary: &, ^, ~, IntFlag, a flag with an alias member, passing the result to a function expecting Literal[F.R].",
     "fuzz/llm-run-2026-10-27 bug-02 (ty Flag union, candidate)",
     strip_leading_comments(git("bug-02-enums-ty-flag-or-literal-union.py"))),
    ("d3p_enums_flag_is_narrowing_else", "enums_literals",
     "mypy expands enum.Flag into its members for `is` narrowing, so the else branch is unreachable and unchecked, although F.R | F.W is neither member. Vary: ==, match statement, `in (F.R, F.W)`, IntFlag, a parameter vs a local variable.",
     "fuzz/llm-run-2026-10-27 bug-06 (mypy Flag is-narrowing, candidate)",
     strip_leading_comments(git("bug-06-enums-mypy-flag-is-narrowing-else-unreachable.py"))),
    ("d3p_typeddict_generic_typevar_unsolved", "typeddict",
     "ty cannot solve T from a generic TypedDict argument (Resp[T] gives Unknown), so two bad assignments pass silently; mypy and pyright report them. Vary: PEP 695 `class Resp[T](TypedDict)`, nested generic TypedDict, NotRequired[T] field, Unpack in kwargs.",
     "fuzz/llm-run-2026-10-27 bug-05 (ty generic TypedDict, candidate)",
     strip_leading_comments(git("bug-05-typeddict-ty-generic-typeddict-typevar-unknown.py"))),
    ("d3p_narrowing_builtin_stale_alias_condition", "narrowing_builtin",
     "An aliased condition (`is_none = a.x is None`) is reused after a method call that mutates a.x; the checker must not narrow through the stale alias. Vary: a walrus alias, alias of isinstance, alias reassigned in a loop, mutation through a property.",
     "kiro_sa/calibration/must_stay_live/mypy_stale_alias.py (calibration: must stay live)", (ML / "mypy_stale_alias.py").read_text()),
    ("d3p_tuples_unpacking_constant_fold_subclass", "tuples_unpacking",
     "ty constant-folds a comparison on a tuple subclass that overrides __lt__, inferring Literal[False] while CPython prints True. Vary: __eq__, __add__, __getitem__ or __len__ overridden on the tuple subclass, NamedTuple subclass, int or str subclass.",
     "kiro_sa/calibration/must_stay_live/ty_constant_fold_tuple_subclass.py (calibration: must stay live)",
     (ML / "ty_constant_fold_tuple_subclass.py").read_text()),
]
for name, area, hyp, origin, body in items:
    text = f"# area: {area}\n# hypothesis: {hyp}\n# origin: {origin}\n{body.rstrip()}\n"
    (H / f"{name}.py").write_text(text)
print(len(items), "written")
