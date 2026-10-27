from typing import Any, reveal_type


class NonData:
    def __get__(self, obj: Any, owner: Any = None) -> int:
        return 1


class C:
    x = NonData()


c = C()
reveal_type(c.x)
c.x = 99  # type: ignore
print(c.x)
print(C.x)
reveal_type(C().x)
