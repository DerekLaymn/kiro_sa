# ajay_examples

These are 40 standalone programs, each probing a different part of ty's type system. Every file runs cleanly on **CPython 3.13**. Lines a spec-conformant checker should reject are marked `# expect-error`, and the ones that would crash are wrapped in `try/except`. Comments next to `reveal_type` give the expected type. These programs have not been run through ty or mypy yet.

```bash
typediff --python-version 3.13 --no-pyright --no-reduce seeds examples/ajay_examples
typediff triage typediff_out
```

| file | area | explores |
|---|---|---|
| `01_typevartuple_shapes.py` | typevartuple_unpack | TypeVarTuple in a generic class, prepending a dimension, *Ts in Callable parameters |
| `02_paramspec_generic_class.py` | paramspec_concatenate | ParamSpec as a class type parameter; P.args/P.kwargs stored and replayed later |
| `03_newtype_annotated.py` | gradual_any (type forms) | NewType is a distinct subtype of its base; Annotated metadata is transparent to checkers |
| `04_literalstring.py` | enums_literals | PEP 675 LiteralString - literals and literal-derived strings are accepted, arbitrary str is not |
| `05_noreturn_reachability.py` | narrowing_builtin | NoReturn calls end control flow; narrowing continues after them; Never in exhausted branches |
| `06_assert_never_exhaustive.py` | narrowing_builtin | exhaustiveness over a union type alias with isinstance + assert_never (and a forgotten case) |
| `07_slots.py` | descriptors_properties | __slots__ restricts instance attributes; slot attributes are descriptors on the class |
| `08_abstract_classes.py` | abstract_classes | abstract methods and abstract properties; instantiating abstract classes; type[Abstract] |
| `09_cached_property_partial.py` | descriptors_properties / callables | functools.cached_property and functools.partial typing |
| `10_context_managers.py` | async_generators | contextlib.contextmanager / asynccontextmanager target types, suppress() |
| `11_flag_strenum.py` | enums_literals | enum.Flag combination, StrEnum values and comparison with plain str, iterating an enum |
| `12_generic_namedtuple.py` | tuples_unpacking | generic NamedTuple (3.11+), unpacking, _replace, solving T from mixed arguments |
| `13_init_subclass_class_getitem.py` | constructors_metaclasses | __init_subclass__ keyword arguments in class statements; custom __class_getitem__ |
| `14_type_of_t.py` | generics_variance | type[T] with an upper bound, unions of class objects, type(obj) round-trips |
| `15_isinstance_tuples_unions.py` | narrowing_builtin | isinstance with a tuple of classes and with a `X | Y` union object; issubclass on type[...] |
| `16_hasattr_callable_narrowing.py` | narrowing_builtin | hasattr() and callable() narrowing |
| `17_match_mapping_guards.py` | match_statement | mapping patterns with **rest, class patterns inside mappings, guards, OR patterns, star captures |
| `18_exception_groups.py` | inheritance_mro (exceptions) | except* narrowing to ExceptionGroup[...], ExceptionGroup.subgroup |
| `19_overloaded_getitem.py` | overloads | overloaded __getitem__ (int vs slice) on a generic Sequence subclass; inherited mixin methods |
| `20_operator_overloading.py` | callables (operators) | __add__/__mul__/__rmul__, NotImplemented fallback to __radd__, sum() with a custom start |
| `21_truthiness_narrowing.py` | narrowing_builtin | truthiness narrowing (if x / not x), `or`/`and` result types, __bool__ returning Literal[False] |
| `22_final_classvar_rules.py` | final_classvar | Final at module/class/instance level, Final inside a loop, `global` reassignment, ClassVar[T] |
| `23_typeguard_vs_typeis.py` | narrowing_user | TypeGuard may narrow to a non-subtype (list[object] -> list[str]); TypeIs may not; methods as guards |
| `24_typeddict_required_inheritance.py` | typeddict | Required inside total=False, NotRequired in a base, TypedDict inheritance and structural subtyping |
| `25_parameter_kinds.py` | callables | positional-only, keyword-only, *args/**kwargs types, defaults, and invalid call shapes |
| `26_self_dataclass_protocol.py` | self_classmethods | Self in dataclass fields and methods (incl. dataclasses.replace), Self-returning protocols |
| `27_total_ordering.py` | inheritance_mro (synthesized methods) | functools.total_ordering synthesizes __ge__ etc.; sorted()/max() need SupportsRichComparison |
| `28_property_setter_types.py` | descriptors_properties | asymmetric property (setter accepts a wider type), deleter, read-only property assignment, |
| `29_generic_classmethods.py` | generics_variance | classmethods on generic classes (Box.of, Box[str].of), classmethods on a specialized subclass, |
| `30_closures_nonlocal.py` | narrowing_builtin (scopes) | narrowing visible in closures, rebinding after a lambda captures a variable (unsound), |
| `31_comprehension_scoping.py` | gradual_any (inference) | dict/set/list/generator comprehension inference, nested comprehensions, walrus binding to the |
| `32_version_platform_checks.py` | narrowing_builtin (reachability) | sys.version_info / sys.platform branches, TYPE_CHECKING-only imports, unreachable imports |
| `33_overloaded_methods_classmethods.py` | overloads | overloads on methods keyed by Literal keyword flags, overloaded classmethods returning Self, |
| `34_recursive_protocols.py` | protocols | protocols using Self in a parameter, recursive protocol properties, bounded TypeVar on a protocol |
| `35_pep695_type_aliases.py` | recursive_aliases | generic `type` aliases (TypeVar, ParamSpec), recursive generic aliases, alias runtime objects |
| `36_asyncio_gather_taskgroup.py` | async_generators | asyncio.gather tuple inference, gather(*list), TaskGroup tasks, wait_for, awaiting a non-awaitable |
| `37_collections_inference.py` | gradual_any (inference) | dict literal inference with int/float values, get/setdefault overloads, defaultdict, Counter, |
| `38_metaclass_methods.py` | constructors_metaclasses | metaclass __getitem__ (class subscription), metaclass properties and __len__ on the class, |
| `39_numeric_promotion.py` | gradual_any (special types) | int -> float -> complex promotion, isinstance(x, int) on a float parameter, builtin numeric |
| `40_dataclass_ordering_slots.py` | dataclasses | dataclass(order=True) comparisons, slots=True, frozen hashing, __match_args__, field(init=False) |
