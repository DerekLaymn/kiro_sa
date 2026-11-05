class L:
    def __mul__(self, other: object) -> int:
        return 1


class R(L):
    def __rmul__(self, other: object) -> str:
        return "s"


s: str = L() * R()   # no error, as it should be
print(type(L() * R()).__name__)
