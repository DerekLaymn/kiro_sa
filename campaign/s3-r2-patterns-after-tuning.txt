live findings in tuning: 5870 in 668 patterns

| # | n | kind | key | has expectation comment | CPython raised | example |
|---|---|---|---|---|---|---|
| 1 | 510 | reveal_mismatch | gradual  | 492 | 66 | mypy__check_functions__testTypeVarIdClashPolymorphic.py |
| 2 | 444 | reveal_mismatch | uncomparable  | 419 | 6 | ty__bidirectional__8.py |
| 3 | 403 | reveal_mismatch | different  | 395 | 6 | ty__exception__control_flow__89.py |
| 4 | 297 | reveal_mismatch | ty_more_precise  | 293 | 2 | ty__narrow__conditionals__is__35.py |
| 5 | 197 | only_mypy | assignment incompatible types in assignment (expression has type _, variable has type _) | 63 | 1 | conformance__typeddicts_extra_items.py |
| 6 | 197 | only_mypy | assert-type expression is of type _, not _ | 1 | 2 | conformance__typeddicts_extra_items.py |
| 7 | 157 | only_ty | type-assertion-failure type _ does not match asserted type _ | 0 | 0 | pyright__tupleLiteralInference4.py |
| 8 | 129 | only_ty | unresolved-reference name _ used when not defined | 33 | 50 | mypy__check_classes__testForwardReferencesInNewTypeMRORecomputed.py |
| 9 | 118 | only_mypy | arg-type argument n to _ has incompatible type _; expected _ | 23 | 2 | ty__narrow__conditionals__is__35.py |
| 10 | 114 | concern_mismatch | assignment incompatible types in assignment (expression has type _, variable has type _) | 70 | 7 | mypy__check_basic__testImplicitInheritInitFromObject.py |
| 11 | 94 | only_ty | invalid-assignment object of type _ is not assignable to _ | 14 | 0 | pyright__type1.py |
| 12 | 86 | only_ty | invalid-argument-type argument to function _ is incorrect: expected _, found _ | 3 | 0 | pyright__tupleLiteralInference4.py |
| 13 | 83 | only_mypy | no-redef name _ already defined on line n | 13 | 1 | ty__subscript__class__5.py |
| 14 | 72 | only_mypy | valid-type variable _ is not valid as a type | 4 | 0 | pyright__type1.py |
| 15 | 69 | reveal_mismatch | mypy_more_precise  | 68 | 2 | ty__narrow__type_guards__42.py |
| 16 | 67 | only_ty | invalid-return-type return type does not match returned value: expected _, found _ | 0 | 0 | pyright__type1.py |
| 17 | 62 | only_mypy | attr-defined _ has no attribute _ | 32 | 10 | conformance__typeddicts_extra_items.py |
| 18 | 47 | only_mypy | has-type cannot determine type of _ | 44 | 4 | ty__invalid_syntax__10.py |
| 19 | 46 | only_mypy | name-defined name _ is not defined | 16 | 2 | ty__scopes__class_implicit_attrs__1.py |
| 20 | 45 | runtime_miss |   | 1 | 44 | typeshed__email__check_parser.py |
| 21 | 43 | concern_mismatch | arg-type argument n to _ has incompatible type _; expected _ | 28 | 6 | pyright__constructor4.py |
| 22 | 42 | only_mypy | overload-cannot-match overloaded function signature n will never be matched: signature n's parameter type(s) are the same or broader | 1 | 0 | pyright__overloadCall6.py |
| 23 | 39 | only_ty | empty-body function always implicitly returns _, which is not assignable to return type _ | 1 | 0 | mypy__check_abstract__testReadWriteAbstractProperty.py |
| 24 | 32 | only_mypy | call-arg unexpected keyword argument _ for _ of _ | 1 | 2 | conformance__typeddicts_extra_items.py |
| 25 | 32 | only_ty | type-assertion-failure,unsupported-operator type _ does not match asserted type _ | 0 | 0 | pyright__tupleComparisonResults9.py |
