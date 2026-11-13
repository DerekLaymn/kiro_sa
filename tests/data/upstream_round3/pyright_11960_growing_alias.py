type GrowingList[T] = list[GrowingList[T | GrowingList[T]]]


def f(x: GrowingList[int]): pass
