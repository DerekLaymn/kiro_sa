# area: descriptors_properties
# explores: asymmetric property (setter accepts a wider type), deleter, read-only property assignment,
# and whether the checker narrows a property to the assigned type (it should not)
from typing import reveal_type


class Temperature:
    def __init__(self) -> None:
        self._c = 0.0

    @property
    def celsius(self) -> float:
        return self._c

    @celsius.setter
    def celsius(self, value: float | str) -> None:
        self._c = float(value)

    @celsius.deleter
    def celsius(self) -> None:
        self._c = 0.0

    @property
    def kelvin(self) -> float:
        return self._c + 273.15


t = Temperature()
t.celsius = "21.5"
reveal_type(t.celsius)  # float (the getter type, not str)
del t.celsius
print(t.celsius, t.kelvin)
try:
    t.celsius = [1]  # expect-error: list is not float | str
except TypeError as exc:
    print("runtime:", exc)
try:
    t.kelvin = 3  # expect-error: read-only property
except AttributeError as exc:
    print("runtime:", exc)
