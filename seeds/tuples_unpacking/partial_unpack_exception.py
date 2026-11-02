# area: tuples_unpacking
# hypothesis: an exception in a later unpacking target must preserve earlier stores
# runtime: deliberately raises AttributeError after catching the unpacking ValueError
def run(items: tuple[int, ...]) -> None:
    value: int | str = 1
    try:
        value, (a, b) = "bad", items
    except ValueError:
        print(value.bit_length())


run((1,))
