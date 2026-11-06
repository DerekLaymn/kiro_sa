from contextlib import suppress


def get(d: dict[str, int]) -> int:
    with suppress(KeyError):
        return d["a"]


print(get({"a": 1}), get({}))
