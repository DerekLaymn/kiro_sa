# area: match_statement
# explores: mapping patterns with **rest, class patterns inside mappings, guards, OR patterns, star captures
from typing import reveal_type


def route(event: dict[str, object]) -> str:
    match event:
        case {"type": "click", "x": int(x), "y": int(y)}:
            reveal_type(x)  # int
            return f"click {x},{y}"
        case {"type": "key", "key": str() as k, **rest}:
            reveal_type(k)  # str
            reveal_type(rest)  # dict[str, object]
            return f"key {k} {len(rest)}"
        case {"type": str(t)} if t.startswith("sys"):
            return f"system {t}"
        case _:
            return "unknown"


def classify(v: int | str | list[int]) -> str:
    match v:
        case 0 | 1:
            reveal_type(v)  # int (Literal[0, 1])
            return "bit"
        case int(n) if n < 0:
            return "negative"
        case [first, *others]:
            reveal_type(first)  # int
            reveal_type(others)  # list[int]
            return f"list {first}"
        case str() | int():
            return "other"
        case []:
            return "empty"


events: list[dict[str, object]] = [
    {"type": "click", "x": 1, "y": 2},
    {"type": "key", "key": "a", "mod": "ctrl"},
    {"type": "sysboot"},
    {},
]
print([route(e) for e in events], classify(1), classify(-3), classify([4, 5]), classify("s"), classify([]))
