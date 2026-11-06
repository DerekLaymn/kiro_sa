# area: gradual_any
# hypothesis: An Any value passed into an int-annotated function and cast to int is still a str at runtime, so checkers must not treat object and Any as interchangeable.
# origin: runs/day10/parents/R_reserve/rsv_gradual_any_76921a4b.py
# area: gradual_any
# hypothesis: An Any value passed into an int-annotated function and cast to int is still a str at runtime, so checkers must not treat object and Any as interchangeable.
from typing import Any, assert_type, cast, reveal_type


def as_int(n: int) -> int:
    return n


def as_object(o: object) -> object:
    return o


def needs_str(s: str) -> str:
    return s.upper()


def try_needs_str(o: object) -> str:
    try:
        return needs_str(o)  # expect-error
    except TypeError:
        return 'rejected'


def flow_any(a: Any) -> int:
    v = as_int(a)
    return v


raw: Any = 'text'
result = flow_any(raw)
assert_type(result, int)
reveal_type(result)
assert isinstance(result, str)
wrong = cast(int, raw)
assert_type(wrong, int)
assert not isinstance(wrong, int)
obj = as_object(raw)
assert_type(obj, object)
reveal_type(obj)
text = try_needs_str(raw)
assert text == 'TEXT'
