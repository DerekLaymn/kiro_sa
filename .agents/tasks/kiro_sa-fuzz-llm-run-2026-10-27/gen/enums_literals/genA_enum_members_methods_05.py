from typing import reveal_type  # noqa

from enum import Enum


class Planet(Enum):
    MERCURY = (3.3e23, 2.4e6)
    EARTH = (5.9e24, 6.3e6)

    def __init__(self, mass: float, radius: float) -> None:
        self.mass = mass
        self.radius = radius

    @property
    def gravity(self) -> float:
        return self.mass / (self.radius * self.radius)

    @classmethod
    def heaviest(cls) -> "Planet":
        return max(cls, key=lambda p: p.mass)


def go() -> None:
    reveal_type(Planet.EARTH.mass)
    reveal_type(Planet.EARTH.value)
    reveal_type(Planet.heaviest())
    reveal_type(Planet.EARTH.gravity)
    reveal_type(list(Planet))
    reveal_type(Planet.__members__)
    reveal_type(len(Planet))
    print(Planet.heaviest())


go()
