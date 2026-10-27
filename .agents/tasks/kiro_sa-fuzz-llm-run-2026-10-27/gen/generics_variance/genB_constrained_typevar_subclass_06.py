from typing import reveal_type


class MyStr(str):
    pass


def dbl[T: (int, str)](x: T) -> T:
    return x + x  # type: ignore[operator]


reveal_type(dbl(MyStr("a")))
reveal_type(dbl(True))
print(dbl(MyStr("a")), dbl(True))
