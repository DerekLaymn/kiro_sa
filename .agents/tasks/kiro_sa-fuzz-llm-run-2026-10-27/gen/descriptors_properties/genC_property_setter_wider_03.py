from typing import reveal_type


class Temp:
    def __init__(self) -> None:
        self._c = 0.0

    @property
    def celsius(self) -> float:
        return self._c

    @celsius.setter
    def celsius(self, v: float | str) -> None:
        self._c = float(v)


t = Temp()
t.celsius = "21.5"
reveal_type(t.celsius)
print(t.celsius)
t.celsius = 3
print(t.celsius)
t.celsius += 1
print(t.celsius)
try:
    t.celsius = None  # type: ignore
except TypeError:
    print("TypeError")
