# area: constructors_metaclasses
# origin: ruff mdtest call/constructor.md block 21
class C[T]:
    __new__: type["C[T]"]

    def __init__(self, x: T):
        pass

reveal_type(C[int](1))  # revealed: C[int]
# error: [invalid-argument-type]
C[int]("wrong")
