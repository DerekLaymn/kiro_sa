from typing import reveal_type


class Stack[T]:
    def __init__(self) -> None:
        self.items: list[T] = []

    @classmethod
    def make(cls) -> "Stack[T]":
        return cls()

    def push(self, x: T) -> None:
        self.items.append(x)


s = Stack[int].make()
reveal_type(s)
s.push(1)
s.push("x")  # error
t = Stack.make()
reveal_type(t)
