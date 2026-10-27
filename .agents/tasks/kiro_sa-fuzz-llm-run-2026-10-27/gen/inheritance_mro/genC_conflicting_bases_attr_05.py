from typing import reveal_type


class A:
    x: int = 1

    def m(self) -> int:
        return 1


class B:
    x: str = "b"

    def m(self) -> str:
        return "b"


class C(A, B):  # type: ignore
    pass


c = C()
reveal_type(c.x)
reveal_type(c.m())
print(c.x, c.m())
class D(B, A):  # type: ignore
    pass
reveal_type(D().x)
print(D().m())
