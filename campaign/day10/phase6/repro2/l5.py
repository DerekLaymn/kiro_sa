from typing import Protocol


class Sink(Protocol):
    def __call__(self, value: int) -> None: ...


def call_by_keyword(sink: Sink) -> None:
    sink(value=1)


def named_x(x: int) -> None:
    print("x", x)


call_by_keyword(lambda value: print("value", value))  # fine
call_by_keyword(named_x)  # def with another name
call_by_keyword(lambda x: print("x", x))  # lambda with another name
