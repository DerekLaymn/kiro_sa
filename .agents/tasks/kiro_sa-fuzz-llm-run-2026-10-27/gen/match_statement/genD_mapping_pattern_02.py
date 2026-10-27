from typing import Any, TypedDict, reveal_type


class Cmd(TypedDict):
    kind: str
    n: int


def f(d: dict[str, int] | Cmd | list[int]) -> int:
    match d:
        case {"kind": k, "n": n}:
            reveal_type(d)
            reveal_type(k)
            reveal_type(n)
            return n
        case {"a": a, **rest}:
            reveal_type(a)
            reveal_type(rest)
            return a + len(rest)
        case {}:
            reveal_type(d)
            return 0
        case _:
            reveal_type(d)
            return -1


def g(d: dict[str, Any]) -> int:
    match d:
        case {"x": int(v)}:
            reveal_type(v)
            return v
        case {"x": str(s)}:
            reveal_type(s)
            return len(s)
    return 0


print(f({"kind": "k", "n": 2}), f({"a": 1, "b": 2}), f({}), f([1]), f({"z": 1}))
print(g({"x": 3}), g({"x": "ab"}), g({}))
