def accept(value: object) -> int:
    if isinstance(value, list):
        value.append("anything")
        return len(value)
    return 0


print(accept([1]), accept(2))
