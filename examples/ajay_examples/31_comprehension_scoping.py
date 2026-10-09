# area: gradual_any (inference)
# explores: dict/set/list/generator comprehension inference, nested comprehensions, walrus binding to the
# enclosing scope, comprehension variables not leaking
from typing import reveal_type

words = ["apple", "bob", "kiwi"]
lengths = {w: len(w) for w in words}
initials = {w[0] for w in words}
pairs = [(i, w) for i, w in enumerate(words) if len(w) > 3]
matrix = [[r * c for c in range(3)] for r in range(2)]
flat = [x for row in matrix for x in row]
gen = (len(w) for w in words)
reveal_type(lengths)  # dict[str, int]
reveal_type(initials)  # set[str]
reveal_type(pairs)  # list[tuple[int, str]]
reveal_type(matrix)  # list[list[int]]
reveal_type(flat)  # list[int]
reveal_type(gen)  # Generator[int, None, None]
if any((longest := w) for w in words if len(w) > 4):
    reveal_type(longest)  # str: the walrus binds in the module scope
print(lengths, sorted(initials), pairs, flat, sum(gen), longest)
try:
    print(w)  # expect-error: comprehension variables do not leak
except NameError as exc:
    print("runtime:", exc)
