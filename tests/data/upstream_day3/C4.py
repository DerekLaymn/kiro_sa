from collections.abc import Callable


def id[T](c: Callable[[T], T]) -> Callable[[T], T]: ...


id(id)
