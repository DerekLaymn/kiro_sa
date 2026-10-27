from typing import reveal_type


def f[*Ts](*args: *Ts, key: int = 0) -> tuple[int, *Ts]:
    return (key, *args)


reveal_type(f("a", 1.0, key=2))
reveal_type(f())
f("a", key="bad")  # error
print(f("a", 1.0, key=2), f())
