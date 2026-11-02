# area: constructors_metaclasses
# origin: ruff mdtest call/constructor.md block 16
class C[T]:
    __new__: type["C[T]"]

# TODO: Default unsolved class type variables in gradual constructor signatures to `Unknown`.
reveal_type(C())  # revealed: C[T@C]
reveal_type(C[int]())  # revealed: C[int]
