# Bug 10 (mypy): see examples/bugs/README.md for the issue link and the expected/actual result.
from contextlib import suppress


def get(d: dict[str, int]) -> int:
    with suppress(KeyError):
        value = d["a"]
    return value


print(get({"a": 1}))
print(get({}))
