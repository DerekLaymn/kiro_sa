from contextlib import suppress


def get(d: dict[str, int]) -> int:
    with suppress(KeyError):
        value = d["a"]
    return value


print(get({"a": 1}))
try:
    print(get({}))
except UnboundLocalError as exc:
    print("UnboundLocalError:", exc)
