from typing import reveal_type


def first_last[F, *M, L](t: tuple[F, *M, L]) -> tuple[F, L]:
    return t[0], t[-1]


reveal_type(first_last((1, "a", 2.0, b"x")))
reveal_type(first_last((1, 2)))
first_last((1,))  # error: too short
print(first_last((1, 2)))
