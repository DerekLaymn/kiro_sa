# area: gradual_any
# origin: ruff mdtest call/type.md block 5
type Meta[T] = type[T]
type NestedMeta[T] = Meta[type[T]]
type Growing[T] = T | NestedMeta[Growing[list[T]]]

def nested_specialization(value: Growing[int]):
    reveal_type(type(value))  # revealed: type[int | type]
