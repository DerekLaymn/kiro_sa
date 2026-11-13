# area: recursive_aliases
# hypothesis: mypy segfaults on PEP 695 aliases whose TypeVarTuple default is the alias itself (type Nested[*Ts = Nested[*Ts]]). Vary: ParamSpec or TypeVar default instead of TypeVarTuple, a list instead of a tuple, mutual recursion between two aliases.
# origin: runs/day2/out3 seed-918936c5da72 (ruff mdtest generics/pep695/aliases.md block 17; live mypy SIGSEGV, narrow upstream matcher did not apply)
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
