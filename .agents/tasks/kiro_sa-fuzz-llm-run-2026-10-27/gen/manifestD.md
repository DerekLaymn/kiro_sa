# Generator D manifest (36 programs; all AST-parse and run under CPython 3.13)

Paths are relative to `.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/`.

| path | area | hypothesis |
|---|---|---|
| narrowing_builtin/genD_isinstance_tuple_types_01.py | narrowing_builtin | isinstance with tuple of classes, plus `and not isinstance(bool)` on object |
| narrowing_builtin/genD_callable_union_02.py | narrowing_builtin | callable() on union with callable instance, type[str] and non-callables |
| narrowing_builtin/genD_hasattr_narrowing_03.py | narrowing_builtin | hasattr() narrowing (synthesized intersection in ty/pyright vs mypy) |
| narrowing_builtin/genD_issubclass_type_04.py | narrowing_builtin | issubclass on type[A]\|type[B] unions, tuple filters, bare `type` |
| narrowing_builtin/genD_len_tuple_union_05.py | narrowing_builtin | len(t)==n on unions of fixed/variadic tuples |
| narrowing_builtin/genD_walrus_early_return_06.py | narrowing_builtin | walrus plus `is None`, continue and for/else narrowing |
| narrowing_builtin/genD_isinstance_generic_alias_08.py | narrowing_builtin | isinstance vs ABCs (Mapping/Sequence) on mixed unions; str/bytes are Sequence |
| narrowing_user/genD_typeis_vs_typeguard_01.py | narrowing_user | TypeIs narrows negative branch, TypeGuard does not; bool subtype of int |
| narrowing_user/genD_typeis_attribute_target_02.py | narrowing_user | TypeIs on attribute and subscript targets; invalidation on assignment |
| narrowing_user/genD_typeis_method_self_03.py | narrowing_user | TypeIs/TypeGuard as method, staticmethod, classmethod; Any argument |
| narrowing_user/genD_typeis_generic_container_04.py | narrowing_user | generic TypeIs[Sequence[T]] / PEP 695 TypeIs[list[T]] on unions |
| narrowing_user/genD_typeguard_negative_noop_05.py | narrowing_user | TypeGuard `not` branch and `and` composition keep the declared type |
| narrowing_user/genD_typeis_final_class_never_06.py | narrowing_user | TypeIs with @final class against disjoint classes yields Never or the original type |
| narrowing_user/genD_typeis_callable_tuple_07.py | narrowing_user | TypeIs to tuple[int,int] and Callable[[int],int] on unions |
| overloads/genD_union_expansion_01.py | overloads | union argument expansion across overloads |
| overloads/genD_any_argument_02.py | overloads | Any argument with differing returns: Any vs first match |
| overloads/genD_union_literal_overlap_03.py | overloads | Literal overlap with str fallback; unions of Literals |
| overloads/genD_generic_overload_04.py | overloads | generic overloads with Sequence/Iterable overlap; default-argument overload |
| overloads/genD_overlap_incompatible_return_05.py | overloads | overlapping overloads with incompatible returns (bool/int, object/str) |
| overloads/genD_method_self_overload_06.py | overloads | Self-returning dunder overloads on subclass; slice vs int |
| overloads/genD_none_default_kwonly_07.py | overloads | keyword-only overloads with None default and bool flag |
| overloads/genD_overload_tuple_star_args_08.py | overloads | `*tuple` unpacking into overloads by arity; `*list` ambiguity |
| match_statement/genD_class_dataclass_positional_01.py | match_statement | dataclass positional patterns skip kw_only fields; nested class/sequence |
| match_statement/genD_mapping_pattern_02.py | match_statement | mapping patterns on dict, TypedDict, list unions; `**rest` |
| match_statement/genD_assert_never_enum_03.py | match_statement | exhaustiveness with assert_never on enum and Literal incl. bool; ends with a runtime-true branch call |
| match_statement/genD_guard_narrowing_04.py | match_statement | guards and narrowing of subject in later cases |
| match_statement/genD_sequence_star_tuple_05.py | match_statement | sequence patterns on tuple unions, star captures, str/bytes excluded |
| match_statement/genD_match_args_custom_06.py | match_statement | custom `__match_args__` order and reachability of later cases |
| match_statement/genD_builtin_class_pattern_07.py | match_statement | builtin class patterns bool(b)/int(i)/str(s) and or-patterns, 0 \| "" |
| async_generators/genD_generator_send_return_01.py | async_generators | Generator send/return types through yield from chain |
| async_generators/genD_async_gen_asend_02.py | async_generators | AsyncGenerator send type, asend(None) first call, aclose |
| async_generators/genD_async_comprehension_await_03.py | async_generators | async comprehensions with await, async genexp type, gather over list[Awaitable] |
| async_generators/genD_asynccontextmanager_04.py | async_generators | asynccontextmanager signature and tuple-unpacking `as` |
| async_generators/genD_yield_from_iterable_05.py | async_generators | yield from in Iterator/Iterable return types; str yielded into Iterator[int] (intended error) |
| async_generators/genD_coroutine_vs_gen_decorator_06.py | async_generators | Awaitable vs Coroutine callable assignability, Task, gather tuple |
| async_generators/genD_async_gen_return_value_07.py | async_generators | anext/aiter types; wrong yield type in async generator (intended error) |

Dropped: narrowing_builtin/genD_is_sentinel_enum_07 (the write was rejected by the user, not retried).
Counts: narrowing_builtin 7, narrowing_user 7, overloads 8, match_statement 7, async_generators 7.
