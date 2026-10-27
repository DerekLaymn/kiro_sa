from typing import reveal_type


class Arr[*Ts]:
    def __init__(self, *dims: *Ts) -> None:
        self.dims = dims

    def prepend(self) -> "Arr[int, *Ts]":
        return Arr(0, *self.dims)


a = Arr("a", 2.0)
reveal_type(a)
b = a.prepend()
reveal_type(b)
reveal_type(b.prepend())
print(b.dims)
