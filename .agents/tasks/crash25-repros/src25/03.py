# area: constructors_metaclasses
# origin: ruff mdtest call/constructor.md block 24
class Meta(type):
    __call__: type["C"]

class C(metaclass=Meta): ...

reveal_type(C())  # revealed: C
