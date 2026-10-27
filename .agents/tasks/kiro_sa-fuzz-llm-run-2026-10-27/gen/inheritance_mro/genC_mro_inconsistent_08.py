from typing import reveal_type


class A:
    def who(self) -> str:
        return "A"


class B(A):
    def who(self) -> str:
        return "B"


try:
    class C(A, B):  # type: ignore
        pass
except TypeError:
    print("TypeError")


class E(B, A, object):
    pass


reveal_type(E().who())
print(E().who(), [k.__name__ for k in E.__mro__])
