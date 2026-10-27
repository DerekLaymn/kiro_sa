# Judge 1 adjudications (fuzz/llm-run-2026-10-27)

Scope taken: the FIRST 9 of the 17 feature-area groups in disagreements.md, in file order:
async_generators, callables, constructors_metaclasses, dataclasses, descriptors_properties,
enums_literals, generics_variance, inheritance_mro, match_statement.
(17 is odd; I took ceil(17/2)=9. Branch 2 should therefore take narrowing_builtin onward: narrowing_builtin, narrowing_user,
overloads, paramspec_concatenate, protocols, tuples_unpacking, typeddict, typevartuple_unpack = 8 groups.)

Judged: 44 cases (programs), covering all 82 review items of those 9 groups.
TRUE BUG: 4 (1 ty, 3 mypy; two are low confidence). KNOWN_DUPLICATE: 4. Everything else: design divergence, spec silent,
or not a real disagreement.

Method. All checkers were re-run by me on the gen/ file (mypy 2.4.0 `--python-version 3.12 --check-untyped-defs --show-error-codes --no-incremental`,
ty 0.0.84 `check --python-version 3.12 --output-format concise`, CPython 3.13.16). Probes were minimised copies in /tmp (p_*.py) run
with `--python-version 3.13`. pyright numbers are from the pipeline records or from my probes (the pyright
run on gen/ files printed only a summary line, so I do not rely on it there). Items that are pure display text (bound-method /
`def` / `Overload[...]` / intersection printing) are judged from the pipeline record plus my re-run reveal lines; I mark them "display".

## TRUE BUG candidates, ranked by confidence

| rank | conf | case | tool | symptom | one-line |
|---|---|---|---|---|---|
| 1 | 0.85 | enums_literals/genA_enum_value_types_02 (20261027-194814-c8a4b97b:D2) | ty | INCORRECT_INFERENCE | `F.R \| F.W` on an `enum.Flag` is revealed `Literal[F.R, F.W]`; runtime value is `<F.R\|W: 3>`, neither member. Spec explicitly exempts Flag from literal expansion. |
| 2 | 0.70 | generics_variance/genB_pep695_callable_attr_variance_04 (20261027-194819-b0b61389:D1) | mypy | FALSE_NEGATIVE | PEP 695 variance inference treats a mutable `Callable[[T], None]` attribute as contravariant; `Handler[float]` accepted as `Handler[int]`; a witness crashes with AttributeError. Plain mutable `T` attribute is correctly invariant (control). |
| 3 | 0.60 | dataclasses/genA_postinit_initvar_07 (20261027-194757-edc14252:D1,D2) | mypy | FALSE_POSITIVE | `Sub.extra` (InitVar with default) flagged `attr-defined`; at runtime `Sub.extra == 0`. ty (`int`) is right. |
| 4 | 0.35 | match_statement/genD_assert_never_enum_03 (20261027-194838-9ebd498c:D1,D4) | mypy (pyright shares it) | FALSE_POSITIVE | `case 1:` does not remove `bool` `True` from the subject, so `assert_never(x)` errors. Runtime: `g(True)` returns "one" (PEP 634 numeric literal patterns compare with `==`). ty's `Never` is right. Low confidence: this is a plausibly known narrowing limitation shared by pyright. |

Real but classified KNOWN_DUPLICATE (not counted above): metaclass `__call__` return ignored by mypy (case 8c4c34d5), `__new__`
return ignored by mypy (43a57668, mypy#15182), mypy accepting an override that renames a positional parameter (bb07d747, mypy#8314),
mypy revealing the function type for class access of `cached_property` (b7be913f).

---

# Per-case verdicts

Format: verdict | faulty tool + symptom | evidence | duplicate note | confidence.

## async_generators (4 cases)

### 20261027-194720-06f0236c genD_async_comprehension_await_03 (D1, D2)
- Verdict: SPEC_AMBIGUITY (display). Both sides are sound; the types differ only in printed class.
- mypy `typing.AsyncGenerator[int, None]`, ty `AsyncGeneratorType[int, None]`; `Coroutine` vs `CoroutineType` likewise. At runtime the objects are `async_generator` / `coroutine` (types.AsyncGeneratorType / CoroutineType), so ty is more precise, mypy is a valid supertype.
- Dup: no KB entry; no AVOID pattern. Confidence 0.8 that it is not a bug.

### 20261027-194727-95d9d021 genD_asynccontextmanager_04 (D1)
- Verdict: FALSE_POSITIVE of pipeline. Same signature `(name: str) -> _AsyncGeneratorContextManager[list[str], None]`, printed with/without `def` and module qualification. Confidence 0.95.

### 20261027-194728-25a34e92 genD_coroutine_vs_gen_decorator_06 (D1, D2, D3)
- D1 (only_mypy `unused-coroutine`): SPEC_AMBIGUITY / design. Not a typing-spec rule; ty has no such check. The warning is valid: CPython printed `RuntimeWarning: coroutine 'leaf' was never awaited` for the same line (run output above). It is ty missing a lint, not a mypy false positive. Not a ty "bug" per the spec.
- D2/D3: display (`Coroutine` vs `CoroutineType`). mypy:
  ```
  genD_coroutine_vs_gen_decorator_06.py:18: error: Value of type "Coroutine[Any, Any, str]" must be used  [unused-coroutine]
  ```
  ty: `Revealed type: CoroutineType[Any, Any, str]` (no diagnostic). Confidence 0.7.

### 20261027-194730-f261f6b1 genD_yield_from_iterable_05 (D1, D2, D3)
- Command output:
  ```
  mypy: :17: error: Function does not return a value (it only ever returns None)  [func-returns-value]
        :18: Revealed type is "None"      :25: Revealed type is "str"
  ty:   :18: Revealed type: `Unknown`     :25: Revealed type: `Unknown`      (line 12, same construct in a(): `str`)
  run:  Runtime type is 'NoneType' (r); x == 'done' (list(c()) printed [1, 2, 'done'] ... via return) 
  ```
- Verdict: SPEC_AMBIGUITY. ty returns `Unknown` (imprecise but gradual, not wrong) for the value of `yield from` when the enclosing function is annotated `Iterator[int]`/`Iterable[int]`, while it infers `str` when annotated `Generator[..., str]`... (line 12 vs 25: both from `inner()`; ty drops it in c()). Imprecision, no unsound claim, so not a bug. mypy's `func-returns-value` on `r = yield from [1, 2]` is a lint on a `None` result, runtime-legal code; mypy design.
- Dup: no. Confidence 0.6 (a ty "could be more precise" report is possible but not a defect by our taxonomy).

## callables (10 cases)

### 20261027-194731-8c7c5337 genB_cb_bound_method_07 (D1, D2): display
- `a: Callable[[int], str] = C().m` ; mypy keeps the declared type, ty/pyright print the narrowed bound method. Narrowing-on-assignment + printing. Pipeline FALSE_POSITIVE. 0.85.

### 20261027-194732-d141e520 genB_cb_callable_in_union_narrow_10 (D1, D2, D3)
- Command output:
  ```
  mypy: Success (reveal def () -> int, then int | str)
  ty:   :7  (int & ((...) -> object)) | (() -> int) | (str & ((...) -> object))
        :8:16 error[invalid-return-type] expected `int`, found `object`
  run:  3 0 0 (no error)
  ```
- Verdict: SPEC_AMBIGUITY (design divergence). After `callable(x)` ty keeps `int & Callable[..., object]` because a subclass of `int` can define `__call__`; its result is `object`, so `return x()` is typed `object`. That is a deliberate sound reading of `callable()` narrowing; mypy/pyright assume int is not callable. The typing spec has no rule for `callable()` narrowing. Runtime cannot distinguish (no int subclass is built). Dup: AVOID_FOR_KB TY-GRADUAL-GENERIC-NARROWING is the neighbour pattern. Confidence 0.75.

### 20261027-194734-ea227106 genB_cb_contravariant_param_04 (D1)
- `g: Callable[[A], B] = takes_b` errors in both mypy and ty (agree). D1 is `reveal_type(f(B()))` where `f: Callable[[B], A] = takes_a`. mypy: declared `A`; ty: narrowed to assigned function's return `B`. Runtime object is `B`. Both sound. KB assignment-narrowing. FALSE_POSITIVE of pipeline. 0.85.

### 20261027-194735-111aded4 genB_cb_default_args_02 (D1), 20261027-194737-d8db1038 genB_cb_kwargs_forward_05 (D1), 20261027-194738-4ea8d8e9 genB_cb_overloaded_to_callable_11 (D1), 20261027-194739-11ffa936 genB_cb_protocol_kwonly_01 (D1)
- All four: variable with a declared Callable/Protocol type assigned a function; mypy reveals declared type, ty/pyright reveal the narrowed assigned type. Declared-type-vs-narrowed-type, no diagnostic disagreement. FALSE_POSITIVE of pipeline (KB assignment narrowing). 0.85.

### 20261027-194740-5f87666c genB_cb_staticmethod_classmethod_08 (D1) and 20261027-194740-ac1c2946 genB_cb_varargs_to_fixed_03 (D1)
- `c.k` printed `bound method type[C].k(n: int) -> int` (ty) vs `def (n: int) -> int`: display text of a bound classmethod (DESIGN.md section 8: weak). `x` in varargs case: declared vs narrowed again. FALSE_POSITIVE of pipeline. 0.85.

### 20261027-202447-6a63fa0a genB_cb_self_attr_callable_12 (D1, D2, D3)
- Command output:
  ```
  mypy: :20 error: Invalid self argument "H" to attribute function "cls_attr" with type "Callable[[int], int]"  [misc]
        :20 Revealed type is "def () -> int"
  ty:   :19 (int, /) -> int   :20 (int, /) -> int      (no diagnostics)
  run:  harness reveals type(h.cls_attr) == 'method' (a plain function in a class attr binds self)
  ```
- Verdict: SPEC_AMBIGUITY, with ty probably unsound for this input. The typing spec's ClassVar section (fetched) says nothing about binding of a `ClassVar[Callable]` that holds a plain function, so there is no verbatim rule. Runtime supports mypy/pyright (bound method; `h.cls_attr(1)` would raise TypeError, which ty accepts). But `ClassVar[Callable[...]]` assigned something that is not a function does not bind, so the declared type is ambiguous. Treat as a well-known mypy#708-style design question. Dup: no KB entry; related known pattern. Confidence 0.55 that ty is wrong in intent but not a defect-by-spec.

## constructors_metaclasses (3 cases)

### 20261027-194745-8c4c34d5 genC_metaclass_call_returns_other_02 (D1-D5, strong D4, D5)
- Command output:
  ```
  mypy: :14 error: Missing positional argument "x" in call to "K"   :15 Revealed type is "...K"
        :16 error: Unsupported operand types for + ("K" and "int")   :18 Revealed type is "...K"
  ty:   :15 Revealed type: `int`    :18 Revealed type: `int`   (no diagnostics)
  run:  type(v) is int, value 42 (metaclass __call__ returns 42; K.__init__ never runs)
  ```
- Spec (constructors.html, fetched): "If the evaluated return type of the __call__ method indicates something other than an instance of the class being constructed, a type checker should assume that the metaclass __call__ method is overriding type.__call__ ... and it should not attempt to evaluate the __new__ or __init__ methods".
- Verdict: mypy is wrong (INCORRECT_INFERENCE plus three FALSE_POSITIVEs: call-arg x2, operator). Strong evidence (runtime + spec). But it is KNOWN_DUPLICATE: FUZZING_PLAN.md already lists `new_returns_other.py` ("mypy reveals Weird / ViaMeta where __new__ / metaclass __call__ return other types; CPython proves mypy wrong ... Probably known; search python/mypy before filing"), same mechanism. Not in known_upstream.json. Confidence that mypy is wrong: 0.9; that it is a duplicate of the pre-existing candidate: 0.75.

### 20261027-194749-43a57668 genC_new_returns_subclass_08 (D1 type-ignore, D2 strong)
- mypy `Revealed type is ...K`, ty/pyright `Other`; run: `<Other object>`. Same shape as above, `__new__` returning a non-subclass. Matches https://github.com/python/mypy/issues/15182 ("Honor return type of __new__ even if not a subclass"): KNOWN_DUPLICATE, mypy INCORRECT_INFERENCE, 0.85. D1 (ty `unused-type-ignore-comment`): mypy needs the ignore when the file is checked strictly; ty does not report the override. Suppression-line config artefact (KB SUPPRESSION-LINE). 0.9.

### 20261027-194742-d8850f11 genC_init_subclass_kwargs_04 (D1-D4)
- Command output:
  ```
  mypy: :10 error: "type[Plugin]" has no attribute "weight"  [attr-defined]   :27 "type[A]" has no attribute "weight" (reveal Any)
  ty:   :27 Revealed type: `int`                                       (no diagnostics)
  run:  prints "2 0 ['a', 'b']"; Runtime type int
  ```
- Verdict: SPEC_AMBIGUITY. `cls.weight = weight` inside `__init_subclass__` creates an attribute that exists at runtime. mypy only infers attributes from `self.x` in methods; ty (and pyright) infer from `cls.x` in classmethods. The spec says nothing about `cls.x` creating declarations. Design divergence (mypy rejects, ty/pyright accept). Dup: no. 0.65.

## dataclasses (3 cases)

### 20261027-194753-8a725af4 genA_generic_dataclass_05 (D1)
- Probe (`Box(1, ["x"])`, ty 0.0.84): `reveal_type -> Box[int | str]`; with a pre-declared `x: list[str]`, `Box(1, x)` errors (`Expected list[int | str], found list[str]`). mypy: `Cannot infer value of type parameter "T"`. pyright errors.
- Verdict: SPEC_AMBIGUITY. ty solves T = `int | str` through bidirectional inference of the list literal, which is a valid (and consistent) solution; the others do not. Spec does not require either. Runtime constructs fine. 0.7.

### 20261027-194754-efdcc08e genA_kw_only_inherit_01 (D1): display only (`c: float =` vs `c: float = ...` vs `= 1`). Same parameter order/kw-only split in all three. FALSE_POSITIVE of pipeline. 0.9.

### 20261027-194757-edc14252 genA_postinit_initvar_07 (D1, D2)  -- TRUE BUG (mypy)
- Command output:
  ```
  mypy: :27 error: "type[Sub]" has no attribute "extra"  [attr-defined]   (reveal Any)
  ty:   :27 Revealed type: `int`
  run (/tmp/p_initvar.py): RES Sub.extra = 0
                           Conf.raw AttributeError type object 'Conf' has no attribute 'raw'
  ```
  `extra: InitVar[int] = 0` leaves `0` as a class attribute (dataclasses keeps the default), so `Sub.extra` is valid and `int`. The control (`Conf.raw`, no default) correctly raises, so the rule is "InitVar with default stays a class attribute". mypy flags valid code (FALSE_POSITIVE) and gives `Any`.
- Dup: not in known_upstream.json/AVOID_FOR_KB; I did NOT search mypy's tracker for this specific pattern. Verdict TRUE BUG, mypy FALSE_POSITIVE, 0.6. (Only runtime evidence; no spec quote.)

## descriptors_properties (2 cases)

### 20261027-194759-b7be913f genC_cached_property_02 (D1, D2)
- D1 ty `unused-type-ignore-comment`: opt-in warning/suppression artefact (KB SUPPRESSION-LINE), FALSE_POSITIVE of pipeline. 0.9.
- D2 `A.value` for `@cached_property`. Probe /tmp/p_cached.py:
  ```
  mypy: :15 Revealed type is "def (self: p_cached.A) -> int"   :16 (A.p, a plain property) Revealed type is "def (self: p_cached.A) -> int"
  ty:   :15 cached_property[int]   :16 property
  run:  RES <class 'functools.cached_property'> False <class 'property'>   (callable(A.value) is False)
  ```
  mypy's revealed callable type cannot be inhabited by the runtime object (a non-callable `cached_property`); ty and pyright are right. mypy gives the same function-type answer for plain `property`, i.e. the long-standing mypy behaviour of treating class access of properties as the function. KNOWN_DUPLICATE (obviously-known mypy property-class-access pattern; I did not find the specific issue number). mypy INCORRECT_INFERENCE, 0.6 for the verdict.

### 20261027-194804-07bd650d genC_property_override_attr_06 (D2): ty `unused-type-ignore-comment`. Same artefact. 0.9.

## enums_literals (4 cases)

### 20261027-194814-c8a4b97b genA_enum_value_types_02 (D1..; strong D2)  -- TRUE BUG (ty)
- Probe /tmp/p_flag.py (class F(enum.Flag): R=1; W=2):
  ```
  mypy:    :11 Revealed type is "p_flag.F"      (a = F.R | F.W)
  ty:      :11 Revealed type: `Literal[F.R, F.W]`   :12 (F.R | F.R) `Literal[F.R]`   :27 (a | F.W) `Literal[F.R, F.W]`
  pyright: Type of "a" is "F"
  run:     RES <F.R|W: 3> False False False      -> a is F.R? False; a is F.W? False; a in (F.R, F.W)? False
  ```
  The runtime value `F.R|W` equals neither listed member, so it cannot inhabit ty's `Literal[F.R, F.W]`. Consequently ty would also treat `if a is F.R or a is F.W: ... else:` as exhaustive (else unreachable), and the else branch runs.
- Spec (enums.html, Enum Literal Expansion): "(This rule does not apply to classes that derive from enum.Flag because these enums allow flags to be combined in arbitrary ways.)"
- Verdict: TRUE BUG, ty, INCORRECT_INFERENCE (reveals a Literal union for a Flag combination; likely derived from literal arithmetic on members). Pipeline KB hint LITERAL-WIDENING does not explain it (the runtime value is outside the type; the pipeline marked this strong).
- Dup: not in known_upstream.json; no AVOID pattern; I did not find an upstream ty issue for it (the search returned nothing relevant). Confidence 0.85.
- The other value reveals in this file (`Literal["a"]` vs `str`, `Literal[2]?` vs `Literal[2]`, tuple literal printing) are mypy-literal-widening vs ty precision, KB LITERAL-WIDENING, both inhabited by runtime values.

### 20261027-194807-208af9db genA_enum_bool_truthy_07 (D1, D3, D4)
- Command output: ty `:21 warning[redundant-condition] Object of type Bit is always truthy`; mypy: Success. run: `Bit.OFF Flagged.NO`.
- Verdict: SPEC_AMBIGUITY. A plain `Enum` without `__bool__`/`__len__` is always truthy even when `Bit.OFF = 0` (true at runtime), so ty's lint is accurate; mypy has `truthy-bool` only when enabled. D3/D4 `Flagged & ~AlwaysFalsy` is display of an accurate (more precise) narrowing. Not a bug. 0.8.

### 20261027-194810-f2f1b453 genA_enum_final_nonmember_06 (D1): display (`def (self: K) -> int` vs `def helper(self) -> int`). 0.95.

### 20261027-194812-13f4ef5e genA_enum_members_methods_05 (D1)
- `Planet.EARTH.value`: mypy `tuple[float, float]`, ty/pyright `Any`; run: `tuple`. Spec (fetched) lists "Literal[1] (or int or object or Any)" as acceptable for enums that set `_value_` in `__init__`. SPEC_AMBIGUITY, ty is less precise but allowed. 0.85.

## generics_variance (6 cases)

### 20261027-194816-bed4617d genB_constrained_union_arg_07 (D1)
- Both mypy (`:9 Value of type variable "T" of "ident" cannot be "int | str"  [type-var]`) and ty (`:9 error[invalid-argument-type] ... does not satisfy constraints (int, str)`) reject; D1 is only the post-error reveal (`int | str` vs `Unknown`). Not a disagreement about the error. The ty behaviour on the call also matches the intended error. FALSE_POSITIVE of pipeline (error recovery display). Dup note: not TY-1090 (that is the reverse direction). 0.85.

### 20261027-194818-1ef16884 genB_invariant_dict_values_10 (D1)
- Both error on lines 10 and 11 (agree). Reveal after a failed assignment: mypy keeps the declared `Mapping[str, float]`, ty the assigned `dict[str, int]`. KB assignment narrowing. FALSE_POSITIVE of pipeline. 0.9.

### 20261027-194819-b0b61389 genB_pep695_callable_attr_variance_04 (D1)  -- TRUE BUG (mypy)
- Source: `class Handler[T]: def __init__(self, cb: Callable[[T], None]): self.cb = cb`; `use(h: Handler[int])`; `hf = Handler[float](...)`; `use(hf)`.
- Commands/outputs:
  ```
  mypy p_handler.py:  Success: no issues found in 1 source file
  ty:      :17 error[invalid-argument-type] Argument to function `use` is incorrect: Expected `Handler[int]`, found `Handler[float]`
  pyright: :17 error: ... Type parameter "T@Handler" is invariant, but "float" is not the same as "int"
  ```
  Witness (/tmp/p_handler.py): `use` does `h.cb = lambda v: print(v.bit_length())`; `hf = Handler[float](lambda x: print(x.is_integer()))`; `use(hf); hf.cb(1.5)`:
  ```
  run: AttributeError: 'float' object has no attribute 'bit_length'     (mypy: Success)
  ```
  Control (/tmp/p_ctrl.py), same mypy:
  ```
  class V[T]: self.v = v (mutable attr of type T)        -> vi: V[int]; vf: V[float] = vi  : error (invariant)   [mypy, ty, pyright agree]
  class CB[T]: self.cb = cb (mutable attr Callable[[T],None]) -> cbf: CB[float]; cbi: CB[int] = cbf : mypy NO error; ty + pyright: invariant error
  class CBF[T]: only a method def call(self, x: T) -> contravariant, OK in all three
  ```
  So mypy infers contravariance for a settable attribute because its type is a Callable (it treats callable-typed attributes like methods).
- Spec (generics.html, Auto variance): variance is inferred by checking whether `ClassA[..., object, ...]` / `ClassA[..., T, ...]` are assignable "using normal assignability rules", which for a mutable attribute requires the attribute type to match (the spec's own example `class ClassA[T1, T2, T3](list[T1])` concludes invariant for T1). The spec example for T2 is a method parameter, not an attribute.
- Verdict: TRUE BUG, mypy, FALSE_NEGATIVE. Related but not the same: python/mypy#14869 (Callable attributes special-cased vs descriptor binding) and #17623 (variance inference for NamedTuple/frozen dataclass). Not in known_upstream.json. Caveat: mypy may defend the Callable-attribute special case as intended (long-standing, see #14869), which lowers confidence. 0.7.

### 20261027-194822-5a240f4d genB_pep695_frozen_covariant_02 (D1, D2)
- D1 `Ro(1)`: mypy `Ro[int]`, ty `Ro[Literal[1]]`, pyright `Ro[int]`. Literal retention when T is inferred covariant: both are subtypes of `Ro[float]`, `f(ri, ...)` passes in both. Inference-choice divergence, SPEC_AMBIGUITY. D2 `si: Sink[int] = Sink[float]()`: declared `Sink[int]` (mypy) vs narrowed `Sink[float]` (ty/pyright): KB assignment narrowing. Both reject `sf: Sink[float] = Sink[int]()` (line 26). 0.8.

### 20261027-194825-360b5d1e genB_typevar_default_pep696_09 (D1)
- All three reject the assignment (mypy on the argument, ty/pyright on the assignment). Only the diagnostic text/code differs (concern mismatch). FALSE_POSITIVE of pipeline, 0.95.

### 20261027-202452-8a6304e4 genB_bound_self_referential_05 (D1..D4)
- Source: `class Cmp(Protocol): def __lt__(self, other: "Cmp", /) -> bool`; `def mx[T: Cmp](a: T, b: T)`; `mx(1, 2)`.
- Re-run (python 3.13 flags, /tmp/p_bound.py): mypy `:13 error: Value of type variable "T" of "mx" cannot be "int"  [type-var]` (also lines 14, 15, 16, 18), ty `invalid-argument-type ... does not satisfy upper bound Cmp` on every call, pyright errors; run prints `2 b 2.5`. 
- Verdict: FALSE_POSITIVE of pipeline for D1-D4. The pipeline record (mypy accepting the calls, reveal `int`) does not reproduce with the same checker and flags; all three agree that the protocol is not satisfied (correct: `int.__lt__` takes `int`, the protocol requires accepting any `Cmp`, so parameter contravariance fails). I could not inspect why the stored mypy result differed (the check command output was lost when my tool channel interleaved with another branch); worth re-running. Confidence 0.7.

## inheritance_mro (5 cases)

### 20261027-194827-34ae8d15 genC_attr_to_readonly_property_04, 20261027-194831-0dde95ca genC_mutable_attr_covariant_override_03, 20261027-194835-77ba6513 genC_override_sync_to_async_07
- Only ty `unused-type-ignore-comment` (the `# type: ignore` is needed by mypy/pyright for an override error that ty does not report here). Suppression-line config artefact (KB SUPPRESSION-LINE; ty warning is opt-in). The question "does ty miss the override error" is TY-2255-adjacent (Self-related) and not testable from this item alone. FALSE_POSITIVE of pipeline, 0.8.

### 20261027-194829-3b66c420 genC_diamond_super_kwargs_01 (D1): display of `super()` (`super` vs `<super: <class 'D'>, Self@who>` vs `Left`). All are printed forms of the same proxy. Display, FALSE_POSITIVE of pipeline, 0.85.

### 20261027-194834-bb07d747 genC_override_param_rename_02 (D1)
- Command output:
  ```
  mypy: Success (no diagnostic on `def f(self, y: int)` overriding `f(self, x: int)`)
  ty:   :10:9 error[invalid-method-override] Invalid override of method `f`: Definition is incompatible with `Base.f`
  pyright: reportIncompatibleMethodOverride
  run:  call(Sub()) -> TypeError (b.f(x=1) on the override)
  ```
- Verdict: mypy FALSE_NEGATIVE with runtime evidence (a keyword call through the `Base` type crashes), but KNOWN_DUPLICATE: https://github.com/python/mypy/issues/8314 "Arg/Kwarg rename passes liskov substitution rule". Not in known_upstream.json (should be added if the run's KB is to dedupe it). ty and pyright are right. Confidence 0.8 on mypy being the outlier; 0.75 that this is exactly #8314.

## match_statement (7 cases)

### 20261027-194838-9ebd498c genD_assert_never_enum_03 (D1, D3, D4)  -- TRUE BUG (low confidence, mypy)
- Minimal probe (/tmp/p_one.py): `def g(x: Literal[1] | bool): match x: case 1: ...; case False: ...; case _: assert_never(x)`
  ```
  mypy:    :11 Revealed type is "Literal[True]"   :12 error: Argument 1 to "assert_never" has incompatible type "Literal[True]"; expected "Never"  [arg-type]
  pyright: :11 Type of "x" is "Literal[True]"       :12 error: ... "Literal[True]" is not assignable to type "Never"
  ty:      :11 Revealed type: `Never`              (no diagnostic)
  run:     RES one f one      (g(True) == "one": `True` is matched by `case 1`, never reaches `_`)
  ```
  PEP 634: a numeric literal pattern matches by `==`, `True == 1`. So the `_` branch is unreachable and `assert_never` is satisfied; mypy and pyright report a false error. D3 (`Literal[1] | bool` vs `Literal[1, True]` vs `bool | Literal[1]`) is just three unions equal as sets of values (KB TY-STRICT-EQUALITY).
- Verdict: TRUE BUG, mypy (shared with pyright), FALSE_POSITIVE, but low confidence (0.35): mypy/pyright may call it a known narrowing incompleteness (the typing spec does not require literal-`1`-excludes-`True` reasoning; the mypy issue #20142 "match-case does not work correctly with Literals vs Enums" is in the same neighbourhood but I did not verify it is the same). The enum half of the file (C.R / C.G | C.B) agrees in both checkers.

### 20261027-194840-b0b45d0c genD_builtin_class_pattern_07 (D2), 20261027-194841-31b252fb genD_class_dataclass_positional_01 (D1, D2), 20261027-194842-20a180d2 genD_guard_narrowing_04 (D1), 20261027-194846-3f1581af genD_sequence_star_tuple_05 (D1)
- ty prints negative-intersection forms (`(int & ~Literal[0] & ~Literal[False]) | (str & ~Literal[""])`, `Q & ~P`, `str & ~AlwaysFalsy`, `tuple[int, ...] & ~tuple[object, *tuple[object, ...], object]`) where mypy/pyright print the positive approximation (`int | str`, `Q`, `str`, `tuple[int, ...]`). All runtime values (`Runtime type is ...`) inhabit both. They are equivalent or ty is more precise. KB TY-GRADUAL-GENERIC-NARROWING (AVOID_FOR_KB). FALSE_POSITIVE of pipeline, 0.85.

### 20261027-194844-50d1934a genD_mapping_pattern_02 (D1-D9)
- Outputs: mypy `k: object | Any`, error `:15 Incompatible return value type (got "object | Any", expected "int")`; ty `k: object`, same error at :15 (`invalid-return-type`); ty keeps `list[int] & Top[Mapping[Unknown, object]]` in the subject (a subclass of list may also be a Mapping), mypy drops list. `Unknown & int` is the display of a TypedDict value capture.
- Verdict: SPEC_AMBIGUITY. Both report the same errors; the reveals differ in precision (pyright is the most precise) and ty's intersection is a sound refinement. No runtime counterexample (runtime values are dict/str/int). 0.7.

### 20261027-194845-3207d5e5 genD_match_args_custom_06 (D1, D2)
- Source: after `case Pt(a, b)` the subject `Pt | int` has only `int` left; `case Pt(x=1)` follows. mypy: line 27 `<subclass of "builtins.int" and "...Pt">`; ty: `Never`; line 30 `int` vs `int & ~Pt`. Runtime: `a1 sub o`, the `Pt(x=1)` branch never executes. Any `int & Pt` instance is already a `Pt` and would have matched `Pt(a, b)` (both sub-patterns are captures), so line 27 is unreachable: ty's `Never` is the more precise correct answer, mypy's intersection is a conservative approximation. KB TY-STRICT-EQUALITY / TY-GRADUAL-GENERIC-NARROWING. SPEC_AMBIGUITY (not a bug). 0.7.

## Summary of dispositions

| class | count (cases) |
|---|---|
| TRUE BUG | 4 (ty: enum Flag `\|`; mypy: callable-attr variance, InitVar-with-default class access, assert_never True/`case 1` [low]) |
| KNOWN_DUPLICATE | 4 (metaclass `__call__` return; `__new__` return mypy#15182; override rename mypy#8314; cached_property class access) |
| SPEC_AMBIGUITY | 12 |
| FALSE_POSITIVE of pipeline (display / assignment narrowing / suppression artefact / error-recovery / not reproducible) | 24 |

(Counts are by primary verdict per case; a few cases carry two verdicts, e.g. the new_returns_subclass and cached_property cases.)

## Housekeeping / caveats
- Not committed, per instructions. Probe files live in /tmp (p_flag.py, p_handler.py, p_ctrl.py, p_initvar.py, p_cached.py, p_one.py, p_bound.py).
- Two tool-channel results (a 16-line json peek and a `cat` merge) were returned out of order because another branch was running commands concurrently; I re-ran the data I needed.
- I did not search upstream trackers for the InitVar item or for the Flag item beyond the single searches noted; "no duplicate found" means none in known_upstream.json/AVOID_FOR_KB and none surfaced in one web search each.
