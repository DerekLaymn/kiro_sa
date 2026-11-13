# area: gradual_any
# hypothesis: A value typed Any flows into an int-annotated function with no runtime check, so cast and assert_type can state int while the object is a str at runtime, and checkers must not treat object and Any as interchangeable.
# origin: llm
# area: gradual_any
# hypothesis: A value typed Any flows into an int-annotated function with no runtime check, so cast and assert_type can state int while the object is a str at runtime, and checkers must not treat object and Any as interchangeable.
from typing import Any, assert_type, cast, reveal_type


def takes_int(n: int) -> int:
    return n


def takes_object(o: object) -> object:
    return o


def gradual(a: Any) -> int:
    v = takes_int(a)
    return v


def use_object(o: object) -> str:
    return o.upper()  # expect-error


raw: Any = 'text'
result = gradual(raw)
assert_type(result, int)
assert isinstance(result, str)
wrong = cast(int, raw)
assert_type(wrong, int)
assert not isinstance(wrong, int)
obj = takes_object(raw)
assert_type(obj, object)
reveal_type(obj)
text = use_object(raw)
assert text == 'TEXT'
