from collections.abc import Callable


class Inst:
    def __init__(self) -> None:
        self.__len__ = lambda: 3
        self.__call__ = lambda: 4
        self.__iter__ = lambda: iter([1])
        self.__getitem__ = lambda i: i
        self.__contains__ = lambda i: True


a = Inst()


def run(label: str, f: Callable[[], object]) -> None:
    try:
        f()
    except TypeError as e:
        print(label, "TypeError:", e)
    else:
        print(label, "ok")


run("len", lambda: len(a))
run("call", lambda: a())
run("iter", lambda: list(a))
run("getitem", lambda: a[0])
run("contains", lambda: 1 in a)
# the same operations as plain statements
len(a)
a()
list(a)
a[0]
1 in a
