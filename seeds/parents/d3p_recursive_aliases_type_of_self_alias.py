# area: recursive_aliases
# hypothesis: A generic alias Meta[T] = type[T] used recursively as `type X = Meta[X]`; mypy segfaults while expanding it. Vary: use list[T] or Callable[[T], T] instead of type[T], add a second alias, make the alias generic in X.
# origin: kiro_sa/.agents/tasks/crash25-repros/mypy_A_typealias_segfault.py (mypy crash)
type Meta[T] = type[T]
type X = Meta[X]
