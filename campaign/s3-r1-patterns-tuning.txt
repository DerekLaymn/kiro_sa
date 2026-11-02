live findings in tuning: 6300 in 667 patterns

| # | n | kind | key | has expectation comment | CPython raised | example |
|---|---|---|---|---|---|---|
| 1 | 623 | reveal_mismatch | gradual  | 602 | 66 | mypy__check_functions__testTypeVarIdClashPolymorphic.py |
| 2 | 552 | reveal_mismatch | different  | 541 | 9 | ty__exception__control_flow__89.py |
| 3 | 476 | reveal_mismatch | uncomparable  | 452 | 6 | ty__bidirectional__8.py |
| 4 | 370 | only_mypy | assignment incompatible types in assignment (expression has type _, variable has type _) | 117 | 1 | mypy__check_expressions__testSimpleConditionalExpression.py |
| 5 | 228 | only_mypy | assert-type expression is of type _, not _ | 1 | 2 | conformance__typeddicts_extra_items.py |
| 6 | 185 | only_ty | type-assertion-failure type _ does not match asserted type _ | 0 | 0 | pyright__tupleLiteralInference4.py |
| 7 | 178 | reveal_mismatch | ty_more_precise  | 176 | 0 | ty__narrow__conditionals__is__35.py |
| 8 | 154 | only_ty | unresolved-reference name _ used when not defined | 56 | 52 | mypy__check_classes__testForwardReferencesInNewTypeMRORecomputed.py |
| 9 | 118 | only_mypy | arg-type argument n to _ has incompatible type _; expected _ | 23 | 2 | ty__narrow__conditionals__is__35.py |
| 10 | 114 | concern_mismatch | assignment incompatible types in assignment (expression has type _, variable has type _) | 70 | 7 | mypy__check_basic__testImplicitInheritInitFromObject.py |
| 11 | 94 | only_ty | invalid-assignment object of type _ is not assignable to _ | 14 | 0 | pyright__type1.py |
| 12 | 86 | only_ty | invalid-argument-type argument to function _ is incorrect: expected _, found _ | 3 | 0 | pyright__tupleLiteralInference4.py |
| 13 | 83 | only_mypy | no-redef name _ already defined on line n | 13 | 1 | ty__subscript__class__5.py |
| 14 | 71 | only_mypy | valid-type variable _ is not valid as a type | 4 | 0 | pyright__type1.py |
| 15 | 67 | only_ty | invalid-return-type return type does not match returned value: expected _, found _ | 0 | 0 | pyright__type1.py |
| 16 | 64 | only_mypy | attr-defined _ has no attribute _ | 33 | 11 | conformance__typeddicts_extra_items.py |
| 17 | 63 | reveal_mismatch | mypy_more_precise  | 63 | 1 | ty__narrow__type_guards__42.py |
| 18 | 47 | only_mypy | has-type cannot determine type of _ | 44 | 4 | ty__invalid_syntax__10.py |
| 19 | 45 | runtime_miss |   | 1 | 44 | typeshed__email__check_parser.py |
| 20 | 45 | only_mypy | name-defined name _ is not defined | 16 | 2 | ty__scopes__class_implicit_attrs__1.py |
| 21 | 43 | concern_mismatch | arg-type argument n to _ has incompatible type _; expected _ | 28 | 6 | pyright__constructor4.py |
| 22 | 42 | only_mypy | overload-cannot-match overloaded function signature n will never be matched: signature n's parameter type(s) are the same or broader | 1 | 0 | pyright__overloadCall6.py |
| 23 | 39 | only_ty | empty-body function always implicitly returns _, which is not assignable to return type _ | 1 | 0 | mypy__check_abstract__testReadWriteAbstractProperty.py |
| 24 | 32 | only_mypy | call-arg unexpected keyword argument _ for _ of _ | 1 | 2 | conformance__typeddicts_extra_items.py |
| 25 | 32 | only_ty | type-assertion-failure,unsupported-operator type _ does not match asserted type _ | 0 | 0 | pyright__tupleComparisonResults9.py |
| 26 | 31 | concern_mismatch | empty-body missing return statement | 0 | 14 | mypy__check_overloading__testUnionMathTrickyOverload2.py |
| 27 | 30 | reveal_unpaired |   | 29 | 1 | ty__narrow__conditionals__is__13.py |
| 28 | 30 | only_mypy | type-arg _ expects no type arguments, but n given | 1 | 0 | mypy__check_semanal_error__testInvalidNumberOfTypeArgs.py |
| 29 | 29 | only_mypy | empty-body missing return statement | 0 | 1 | pyright__descriptor4.py |
| 30 | 27 | only_mypy | misc incompatible return type for _ (returns _, but must return a subtype of _) | 1 | 0 | pyright__constructorCallable2.py |
| 31 | 27 | only_mypy | misc invalid statement in typeddict definition; expected _ | 0 | 0 | pyright__typedDict28.py |
| 32 | 26 | only_mypy | arg-type argument n to _ of _ has incompatible type _; expected _ | 13 | 1 | pyright__tupleLiteralInference4.py |
| 33 | 25 | only_mypy | assignment incompatible types in assignment (expression has type _, base class _ defined the type as _) | 10 | 0 | ty__call__constructor__9.py |
| 34 | 25 | concern_mismatch | arg-type argument n to _ of _ has incompatible type _; expected _ | 19 | 3 | mypy__check_functions__testCallConditionalMethodInClassBody.py |
| 35 | 24 | only_mypy | typeddict-unknown-key extra key _ for typeddict _ | 0 | 0 | conformance__typeddicts_extra_items.py |
| 36 | 24 | only_mypy | operator unsupported operand types for > (_ and _) | 1 | 0 | ty__comparison__intersections__31.py |
| 37 | 24 | only_mypy | misc all conditional function variants must have identical signatures | 12 | 0 | mypy__check_functions__testIncompatibleConditionalMethodDefinition.py |
| 38 | 24 | only_ty | invalid-parameter-default default value of type _ is not assignable to annotated parameter type _ | 0 | 0 | pyright__typeVar8.py |
| 39 | 22 | only_mypy | assert-type,operator expression is of type _, not _ | 0 | 0 | pyright__tupleComparisonResults23.py |
| 40 | 21 | only_ty | assert-type-unspellable-subtype type _ does not match asserted type _ | 0 | 0 | conformance__generics_syntax_scoping.py |
