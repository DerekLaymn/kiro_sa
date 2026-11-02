# area: constructors_metaclasses
# origin: ruff mdtest call/constructor.md block 25
class C:
    __new__: "Factory"

class Factory:
    __call__: type[C]

reveal_type(C())  # revealed: C
