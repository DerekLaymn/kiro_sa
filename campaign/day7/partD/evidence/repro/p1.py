from typing import assert_type, overload


class Clamped:
    @overload
    def __get__(self, instance: None, owner: type) -> "Clamped": ...
    @overload
    def __get__(self, instance: object, owner: type) -> int: ...
    def __get__(self, instance: object | None, owner: type) -> "Clamped | int":
        if instance is None:
            return self
        return 0

    def __set__(self, instance: object, value: int) -> None:
        pass


class Gauge:
    level = Clamped()

    def __init__(self, start: int) -> None:
        self.level = start


assert_type(Gauge.level, Clamped)
assert_type(Gauge(1).level, int)
print(type(Gauge.level).__name__)
