# manifestB (generator branch B)

All programs are CPython-unverified: the shell was unavailable, so they were not run. Statements expected to raise at runtime were reviewed by hand and guarded with `if len(sys.argv) > 99:`.

Base: `.agents/tasks/kiro_sa-fuzz-llm-run-2026-10-27/gen/<area>/`

## generics_variance (11)
| file | hypothesis | status |
|---|---|---|
| genB_pep695_mutable_invariant_01.py | PEP695 class with mutable list attr infers invariant; Box[int]->Box[float] errors | CPython-unverified |
| genB_pep695_frozen_covariant_02.py | read-only property infers covariant, method param infers contravariant | CPython-unverified |
| genB_pep695_variance_with_setter_03.py | property with setter makes T invariant | CPython-unverified |
| genB_pep695_callable_attr_variance_04.py | mutable Callable[[T], None] attribute: invariant vs contravariant inference | CPython-unverified |
| genB_bound_self_referential_05.py | TypeVar bound to Protocol with `__lt__(Cmp)`; mixed int/float solving | CPython-unverified |
| genB_constrained_typevar_subclass_06.py | constrained TypeVar with str subclass / bool arg: solves to constraint | CPython-unverified |
| genB_constrained_union_arg_07.py | constrained TypeVar given `int \| str` arg must error | CPython-unverified |
| genB_generic_classmethod_infer_08.py | generic classmethod returning Stack[T]: Stack[int].make vs Stack.make | CPython-unverified |
| genB_typevar_default_pep696_09.py | PEP696 default `V = int` with partial specialization and mismatched construction | CPython-unverified |
| genB_invariant_dict_values_10.py | dict to Mapping: value covariant, key invariant | CPython-unverified |
| genB_variance_inheritance_override_11.py | subclass of Producer[int] passed as Producer[float] (inferred covariance) | CPython-unverified |

## paramspec_concatenate (10)
| file | hypothesis | status |
|---|---|---|
| genB_concat_decorator_inject_01.py | Concatenate injection drops first param; kw-only remainder | CPython-unverified |
| genB_concat_pos_only_prefix_02.py | Concatenate[int, P] on `(x, y)`: remainder y callable by keyword | CPython-unverified |
| genB_paramspec_add_param_03.py | wrapper prepends positional-only bool via Concatenate return | CPython-unverified |
| genB_paramspec_method_decorator_04.py | Concatenate[S, P] on methods preserves self binding | CPython-unverified |
| genB_paramspec_stacked_decorators_05.py | stacked drop/add decorators; resulting signature order | CPython-unverified |
| genB_paramspec_args_kwargs_mismatch_06.py | forwarding only `*args: P.args` without kwargs must error | CPython-unverified |
| genB_paramspec_class_generic_07.py | generic class Task[**P, R] with `__call__`/method using P.args | CPython-unverified |
| genB_paramspec_ellipsis_assign_08.py | Task[[int], int] to Task[..., int] OK, to Task[[str], int] error | CPython-unverified |
| genB_paramspec_lambda_pass_09.py | lambda with default through ParamSpec identity | CPython-unverified |
| genB_paramspec_kwonly_remainder_10.py | remainder after Concatenate is keyword-only; positional call errors | CPython-unverified |

## typevartuple_unpack (10)
| file | hypothesis | status |
|---|---|---|
| genB_tvt_args_to_tuple_01.py | `*args: *Ts` to `tuple[*Ts]`, including empty call | CPython-unverified |
| genB_tvt_prefix_suffix_02.py | `tuple[F, *M, L]` with too-short tuple must error | CPython-unverified |
| genB_tvt_class_array_03.py | generic `Array[*Shape]` constructor inference and mismatched annotation | CPython-unverified |
| genB_tvt_unbounded_tuple_04.py | TypeVarTuple matched against `tuple[int, ...]` and `tuple[int, *tuple[str, ...]]` | CPython-unverified |
| genB_tvt_callable_args_05.py | `Callable[[*Ts], R]` with matching `*args: *Ts` | CPython-unverified |
| genB_tvt_two_tuples_concat_06.py | two TypeVarTuples concatenated in return | CPython-unverified |
| genB_tvt_unpack_alias_07.py | PEP695 alias `Row[*Ts]` specialized with args, `()`, and Unpack of unbounded tuple | CPython-unverified |
| genB_tvt_args_kwargs_mix_08.py | keyword-only param after `*args: *Ts` | CPython-unverified |
| genB_tvt_zip_len_mismatch_09.py | same `*Ts` bound to different-length tuples: error vs join | CPython-unverified |
| genB_tvt_method_self_shape_10.py | method returning `Arr[int, *Ts]` (prepend) | CPython-unverified |

## callables (12)
| file | hypothesis | status |
|---|---|---|
| genB_cb_protocol_kwonly_01.py | callback protocol kw-only param name must match | CPython-unverified |
| genB_cb_default_args_02.py | default args and Callable arity assignability | CPython-unverified |
| genB_cb_varargs_to_fixed_03.py | `*args: int` fits fixed arity; fixed does not fit larger arity | CPython-unverified |
| genB_cb_contravariant_param_04.py | param contravariance / return covariance | CPython-unverified |
| genB_cb_kwargs_forward_05.py | `**kwargs: int` satisfies named kw-only protocol; `**kwargs: str` does not | CPython-unverified |
| genB_cb_class_as_callable_06.py | class object as Callable via `__init__` signature | CPython-unverified |
| genB_cb_bound_method_07.py | bound vs unbound method assignability | CPython-unverified |
| genB_cb_staticmethod_classmethod_08.py | static/classmethod via instance and class as Callable | CPython-unverified |
| genB_cb_generic_returning_callable_09.py | generic function returning Callable[[T], T] with literal solving | CPython-unverified |
| genB_cb_callable_in_union_narrow_10.py | `callable()` narrowing on `int \| Callable \| str` | CPython-unverified |
| genB_cb_overloaded_to_callable_11.py | overloaded function assigned to Callable (matching, non-matching, union) | CPython-unverified |
| genB_cb_self_attr_callable_12.py | Callable instance attr vs ClassVar[Callable]: self binding differs | CPython-unverified |

Totals: generics_variance 11, paramspec_concatenate 10, typevartuple_unpack 10, callables 12 = 43.
