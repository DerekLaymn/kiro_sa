from typing import reveal_type


class Meta(type):
    def __call__(cls, *args: str) -> int:
        return len(args[0])


class Widget(metaclass=Meta):
    def __init__(self, name: str) -> None:
        self.name = name


n = Widget("abc")
reveal_type(n)
print(type(n).__name__, n)
