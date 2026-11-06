from collections.abc import Callable, Iterator


class Ann:
    __len__: Callable[[], int]
    __call__: Callable[[], int]
    __iter__: Callable[[], Iterator[int]]
    __getitem__: Callable[[int], int]
    __contains__: Callable[[int], bool]


a = Ann()


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
