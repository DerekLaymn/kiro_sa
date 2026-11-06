from collections.abc import Callable, Iterator


class Ann:
    # the callables take the instance as first parameter, as a method would
    __len__: Callable[["Ann"], int]
    __call__: Callable[["Ann"], int]
    __iter__: Callable[["Ann"], Iterator[int]]
    __getitem__: Callable[["Ann", int], int]
    __contains__: Callable[["Ann", int], bool]


a = Ann()
len(a)
a()
list(a)
a[0]
1 in a
