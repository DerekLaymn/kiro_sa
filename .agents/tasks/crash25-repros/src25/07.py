# area: constructors_metaclasses
# origin: ruff mdtest call/constructor.md block 15
class A:
    __new__: type["B"]

class B:
    __new__: type[A]

reveal_type(A())  # revealed: A
