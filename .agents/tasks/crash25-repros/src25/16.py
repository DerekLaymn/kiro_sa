# area: recursive_aliases
# origin: ruff mdtest generics/pep695/aliases.md block 17
# error: [invalid-legacy-type-variable]
# error: [invalid-type-form]
type Nested[*Ts = Nested[*Ts]] = tuple[Nested[*Ts, Nested[*Ts]]]

# error: [invalid-legacy-type-variable]
# error: [invalid-type-form]
type Suffix[*Ts = Suffix[*Ts]] = list[Suffix[*Ts, int]]

# error: [invalid-legacy-type-variable]
# error: [invalid-type-form]
type Prefix[*Ts = Prefix[*Ts]] = tuple[Prefix[int, *Ts]]

type ValidDefault[*Ts = *tuple[ValidDefault[int]]] = tuple[ValidDefault[*Ts, int]]
