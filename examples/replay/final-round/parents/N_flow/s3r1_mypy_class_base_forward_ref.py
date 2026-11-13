# area: gradual_any
# hypothesis: a class defined before its base reads an attribute set later in the base's __init__, with a decorator-deferred function; the checkers disagree on the revealed attribute type. Vary: the forward reference, Optional vs plain attribute, the decorator.
# origin: python/mypy check-newsemanal.test [case testForwardBaseDeferAttr]
from typing import Optional, Callable, TypeVar

class C(B):
    def a(self) -> None:
        reveal_type(self._foo)  # N: Revealed type is "builtins.int | None"
        self._foo = defer()

class B:
    def __init__(self) -> None:
        self._foo: Optional[int] = None

T = TypeVar("T")
def deco(fn: Callable[[], T]) -> Callable[[], T]: ...

@deco
def defer() -> int: ...

