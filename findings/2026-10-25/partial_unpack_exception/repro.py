def run(items: tuple[int, ...]) -> None:
    value: int | str = 1
    try:
        value, (a, b) = "bad", items
    except ValueError:
        print(value.bit_length())


run((1,))
