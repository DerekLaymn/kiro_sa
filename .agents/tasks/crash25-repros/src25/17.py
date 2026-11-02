# area: recursive_aliases
# origin: ruff mdtest pep695_type_aliases.md block 55
type Identity[T] = T
type Cyclic = Identity[Cyclic]  # error: [cyclic-type-alias-definition]

def use(value: Cyclic):
    value[0]
