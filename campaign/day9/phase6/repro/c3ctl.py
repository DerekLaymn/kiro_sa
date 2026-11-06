from typing import reveal_type


class C:
    def __add__(self, other: "C") -> str:
        return "add"

    def __radd__(self, other: "C") -> int:
        return 7


class D(C):
    pass


a = C()
b = C()
reveal_type(a + b)
print(repr(a + b))
reveal_type(a + D())
print(repr(a + D()))
