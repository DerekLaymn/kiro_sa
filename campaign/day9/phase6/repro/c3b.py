from typing import reveal_type


class C:
    def __lt__(self, other: "C") -> str:
        return "lt"

    def __gt__(self, other: "C") -> int:
        return 7


a = C()
b = C()
reveal_type(a < b)
reveal_type(a > b)
print(repr(a < b), repr(a > b))
