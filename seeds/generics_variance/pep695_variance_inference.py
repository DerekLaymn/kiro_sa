# area: generics_variance
# hypothesis: PEP 695 infers variance from usage; read-only -> covariant, mutable -> invariant.
# spec: typing spec, generics.html "Variance inference".
from typing import reveal_type


class ReadOnlyBox[T]:
    def __init__(self, item: T) -> None:
        self._item = item

    def get(self) -> T:
        return self._item


class MutableBox[T]:
    def __init__(self, item: T) -> None:
        self.item = item


class Sink[T]:
    def put(self, item: T) -> None:
        print(item)


ro: ReadOnlyBox[object] = ReadOnlyBox[int](1)  # ok: covariant
mb: MutableBox[object] = MutableBox[int](1)  # expect-error: invariant (public mutable attribute)
sk: Sink[int] = Sink[object]()  # ok: contravariant
sk2: Sink[object] = Sink[int]()  # expect-error
reveal_type(ro.get())
print(ro.get(), mb.item)
sk.put(3)
