from typing import reveal_type  # noqa

def go(t: tuple[int] | tuple[int, str] | tuple[int, str, float]) -> str:
    if len(t) == 2:
        reveal_type(t)
        return t[1]
    if len(t) >= 3:
        reveal_type(t)
        return str(t[2])
    reveal_type(t)
    return str(t[0])


def go2(t: tuple[int, ...]) -> int:
    if len(t) == 2:
        reveal_type(t)
        a, b = t
        return a + b
    return 0


print(go((1,)), go((1, "a")), go((1, "a", 2.0)), go2((1, 2)))
