from typing import reveal_type


class Array[*Shape]:
    def __init__(self, shape: tuple[*Shape]) -> None:
        self.shape = shape

    def get_shape(self) -> tuple[*Shape]:
        return self.shape


a = Array((3, 4))
reveal_type(a)
reveal_type(a.get_shape())
b: Array[int, int, int] = Array((1, 2))  # error
print(a.get_shape(), b)
