from typing import Generator, Iterator, Iterable, reveal_type


def inner() -> Generator[int, None, str]:
    yield 1
    yield 2
    return "done"


def a() -> Generator[int | str, None, None]:
    r = yield from inner()
    reveal_type(r)
    yield r


def b() -> Iterator[int]:
    r = yield from [1, 2]
    reveal_type(r)
    yield from range(2)
    yield from "ab"  # str not int


def c() -> Iterable[int]:
    x = yield from inner()
    reveal_type(x)
    return x  # type: ignore[return-value]


print(list(a()), list(c()))
print(list(b()))
