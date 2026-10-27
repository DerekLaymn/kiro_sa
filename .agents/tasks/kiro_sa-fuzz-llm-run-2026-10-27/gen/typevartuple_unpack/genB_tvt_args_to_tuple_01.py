from typing import reveal_type


def pack[*Ts](*args: *Ts) -> tuple[*Ts]:
    return args


reveal_type(pack(1, "a", 2.5))
reveal_type(pack())
print(pack(1, "a"), pack())
