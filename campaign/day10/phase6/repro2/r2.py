def name(n: int) -> str:
    return str(n)


def run(n: int) -> None:
    if name(n) == 4:
        n.no_such_attribute
        name(n, 1, 2)
        name("not an int")


run(3)
