from typing import reveal_type


def cat[*A, *B](a: tuple[*A], b: tuple[*B]) -> tuple[*A, *B]:
    return (*a, *b)


reveal_type(cat((1, "a"), (2.0,)))
reveal_type(cat((), ()))
print(cat((1, "a"), (2.0,)))
