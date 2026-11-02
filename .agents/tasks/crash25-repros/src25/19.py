# area: gradual_any
# origin: ruff mdtest call/type.md block 4
type Meta[T] = type[T]
type Growing[T] = T | Meta[Growing[list[T]]]

def growing_class(value: Growing[int]):
    reveal_type(type(value))  # revealed: type[int | type]
