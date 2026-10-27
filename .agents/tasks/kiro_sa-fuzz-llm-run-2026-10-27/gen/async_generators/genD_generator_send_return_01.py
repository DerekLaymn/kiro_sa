from typing import Generator, reveal_type


def acc() -> Generator[int, str, bool]:
    s = yield 1
    reveal_type(s)
    t = yield len(s)
    reveal_type(t)
    return t == "end"


def outer() -> Generator[int, str, list[bool]]:
    r1 = yield from acc()
    reveal_type(r1)
    r2 = yield from acc()
    return [r1, r2]


def main() -> None:
    g = outer()
    reveal_type(g.send(None))
    reveal_type(g.send("abc"))
    g.send("end")
    g.send("x")
    try:
        g.send("no")
    except StopIteration as e:
        reveal_type(e.value)
        print(e.value)


main()
