from collections.abc import Callable


def id[**P](c: Callable[P, int]) -> Callable[P, int]: ...


id(id)
