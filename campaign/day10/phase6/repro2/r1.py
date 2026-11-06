def name(n: int) -> str:
    return str(n)


def run(n: int) -> None:
    assert name(n) == 4  # str is never equal to 4, so this fails at runtime
    n.no_such_attribute
    name(n, 1, 2)
    name("not an int")


try:
    run(3)
except AssertionError:
    print("assertion failed")
