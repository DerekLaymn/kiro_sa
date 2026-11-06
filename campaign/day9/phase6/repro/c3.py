from typing import Literal, reveal_type


class C:
    def __lt__(self, other: "C") -> Literal[True]:
        return True

    def __gt__(self, other: "C") -> Literal[False]:
        return False


a = C()
b = C()
reveal_type(a < b)
reveal_type(a > b)
print(a < b, a > b)
