from collections.abc import Callable


def id[**P, R](c: Callable[P, R]) -> Callable[P, R]: ...


reveal_type(id(id))
