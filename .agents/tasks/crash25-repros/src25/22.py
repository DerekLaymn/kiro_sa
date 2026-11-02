# area: constructors_metaclasses
# origin: ruff mdtest call/constructor.md block 22
class C:
    __init__: type["C"]

reveal_type(C())  # revealed: C
