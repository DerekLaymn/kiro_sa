from collections.abc import Callable


def id[**P, R](c: Callable[P, R]) -> Callable[P, R]: ...


def g(x: int) -> str: ...


id(g)
