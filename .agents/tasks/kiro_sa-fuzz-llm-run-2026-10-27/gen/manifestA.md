# manifestA (genA: dataclasses, tuples_unpacking, typeddict, enums_literals)

Base: .agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/

- dataclasses/genA_kw_only_inherit_01.py | dataclasses | KW_ONLY in base then non-kw field in child: checkers may disagree on synthesized __init__ order.
- dataclasses/genA_frozen_inherit_02.py | dataclasses | frozen child assignment and replace() result type may differ in error reporting.
- dataclasses/genA_field_default_factory_03.py | dataclasses | field(init=False)/default_factory typing in synthesized __init__ may differ.
- dataclasses/genA_order_slots_04.py | dataclasses | order=True vs order=False comparison errors and __slots__ reveal may differ.
- dataclasses/genA_generic_dataclass_05.py | dataclasses | generic dataclass with specialized subclass; inference of Box(1, ["x"]) may differ.
- dataclasses/genA_transform_field_specifiers_06.py | dataclasses | dataclass_transform kw_only_default/field_specifiers/frozen_default on metaclass support differs (ty likely weaker).
- dataclasses/genA_postinit_initvar_07.py | dataclasses | InitVar inheritance and __post_init__ signature check; access to Sub.extra may differ.
- dataclasses/genA_match_args_fields_08.py | dataclasses | match_args=False positional pattern errors and fields()/asdict reveals may differ.
- tuples_unpacking/genA_star_unpack_fixed_01.py | tuples_unpacking | star-unpack of fixed tuple: list element type (union vs join) may differ.
- tuples_unpacking/genA_star_unpack_variadic_02.py | tuples_unpacking | star-unpack of tuple[int, *tuple[str, ...], float] and fixed 3-unpack may differ.
- tuples_unpacking/genA_slice_fixed_03.py | tuples_unpacking | slicing fixed tuples with step/negative/empty ranges may yield precise vs tuple[X, ...].
- tuples_unpacking/genA_slice_variadic_04.py | tuples_unpacking | indexing/slicing of mixed variadic tuples handled differently.
- tuples_unpacking/genA_namedtuple_generic_05.py | tuples_unpacking | generic NamedTuple support (_replace, slicing, unpack) differs.
- tuples_unpacking/genA_namedtuple_inherit_06.py | tuples_unpacking | NamedTuple subclass unpack arity mismatch and _make/_fields reveals may differ.
- tuples_unpacking/genA_tuple_concat_mul_07.py | tuples_unpacking | tuple + and * result precision for fixed/variadic may differ.
- tuples_unpacking/genA_tuple_len_narrow_08.py | tuples_unpacking | len() narrowing on union of tuples and on tuple[int, ...] may differ.
- tuples_unpacking/genA_unpack_in_for_nested_09.py | tuples_unpacking | nested/star unpacking in for targets and zip with 3 args may differ.
- typeddict/genA_required_inherit_01.py | typeddict | Required/NotRequired under total=False inheritance and .get() types may differ.
- typeddict/genA_in_narrowing_02.py | typeddict | `in` narrowing on union of TypedDicts and discriminant narrowing may differ (mypy weaker).
- typeddict/genA_readonly_override_03.py | typeddict | ReadOnly mutation via update/setdefault/pop/del reporting differs.
- typeddict/genA_extra_items_04.py | typeddict | PEP 728 extra_items support: mypy vs ty differing acceptance.
- typeddict/genA_structural_assign_05.py | typeddict | structural assignability between TypedDicts, float vs int values, and to dict[str, object].
- typeddict/genA_unpack_kwargs_06.py | typeddict | Unpack[TypedDict] with inherited Required/NotRequired and **o call forwarding.
- typeddict/genA_generic_functional_07.py | typeddict | generic TypedDict inference and functional syntax with keyword key.
- typeddict/genA_key_ops_08.py | typeddict | non-literal key indexing, `|` operator, keys/items/copy reveals differ.
- enums_literals/genA_enum_exhaustive_01.py | enums_literals | is-chain/match exhaustiveness with assert_never on enum members.
- enums_literals/genA_enum_value_types_02.py | enums_literals | StrEnum/IntEnum/Flag/tuple-valued .value and operator reveals differ.
- enums_literals/genA_enum_literal_member_03.py | enums_literals | Literal[Enum.member] unions, `in` tuple narrowing, Mode(lit)/Mode["R"].
- enums_literals/genA_literal_union_narrow_04.py | enums_literals | Literal str exhaustion by == chain and `in` narrowing of Literal ints/str.
- enums_literals/genA_enum_members_methods_05.py | enums_literals | enum with __init__ tuple values, attrs, classmethod, __members__ reveals.
- enums_literals/genA_enum_final_nonmember_06.py | enums_literals | member()/nonmember()/_ignore_/Final inside Enum treated differently.
- enums_literals/genA_enum_bool_truthy_07.py | enums_literals | truthiness narrowing of enums with/without __bool__ and Literal[0,1].
- enums_literals/genA_enum_subclass_mixin_08.py | enums_literals | memberless enum base subclassing and str-mixin Enum assignability to str.
