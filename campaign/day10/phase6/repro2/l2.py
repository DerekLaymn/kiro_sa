from typing import Protocol


class Sink[T](Protocol):
    def __call__(self, value: T) -> None: ...


class Handler[T]:
    def __init__(self, sink: Sink[T]) -> None:
        self.sink: Sink[T] = sink


h = Handler[float](lambda x: print("float", x))
g = Handler[float](lambda value: print("float", value))
h.sink = lambda x: print(x)
g.sink = lambda value: print(value)
print(h, g)
