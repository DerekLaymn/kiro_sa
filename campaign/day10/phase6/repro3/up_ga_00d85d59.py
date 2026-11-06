# area: gradual_any
# hypothesis: An Any value passed to an int parameter type-checks silently, so assert_type can state int while the runtime object is a str, and object does not allow attribute access that Any allows.
# origin: runs/day10/parents/R_reserve/rsv_gradual_any_76921a4b.py
# hypothesis: A value typed Any passed to an int parameter type-checks silently, so assert_type can state int while the runtime object is a str, and object does not allow attribute access that Any allows.
from typing import Any, assert_type, cast, reveal_type


def takes_int(n: int) -> int:
    return n


def takes_int_or_str(n: int | str) -> int | str:
    return n


def from_any(a: Any) -> int:
    v = takes_int(a)
    return v


def use_object(o: object) -> str:
    return o.upper()  # expect-error


raw: Any = 'text'
result = from_any(raw)
assert_type(result, int)
assert isinstance(result, str)
wide = takes_int_or_str(raw)
reveal_type(wide)
assert wide == 'text'
wrong = cast(int, raw)
assert_type(wrong, int)
assert not isinstance(wrong, int)
text = use_object(raw)
assert text == 'TEXT'
