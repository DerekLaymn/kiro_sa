# area: recursive_aliases
# hypothesis: mypy prints the recursive occurrence inside a recursive alias as "...", so reveal_type shows tuple[str, ...] for a 2-tuple, and it does not narrow a declared union on its initial assignment (mypy#2008); ty and pyright narrow to the assigned tuple. The earlier "runtime value does not inhabit mypy's type" evidence came from reading that "..." as a variadic tuple.
# origin: results/bugs.md section 3 (seed-4d6aa9e30260, d3p_crash_mypy_segv_recursive_tvt_default_alias__mut0_9fca6f47)
from typing import reveal_type

type Left = tuple[int, Right] | None
type Right = tuple[str, Left]

sample: Left = (1, ("a", (2, ("b", None))))
reveal_type(sample)


def g(n: Left) -> None:
    if n is not None:
        reveal_type(n[1])
        reveal_type(n[1][1])


g(sample)
print(sample)
