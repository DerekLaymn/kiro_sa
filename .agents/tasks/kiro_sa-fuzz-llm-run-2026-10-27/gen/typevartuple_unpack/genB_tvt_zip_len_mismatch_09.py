from typing import reveal_type


def same_shape[*Ts](a: tuple[*Ts], b: tuple[*Ts]) -> tuple[*Ts]:
    return a


reveal_type(same_shape((1, "a"), (2, "b")))
reveal_type(same_shape((1, "a"), (2, 3)))  # error or join?
print(same_shape((1, "a"), (2, "b")))
