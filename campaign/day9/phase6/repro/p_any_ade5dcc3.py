# area: gradual_any
# hypothesis: Any propagates through attribute access and calls, while an object-typed value rejects attribute access that Any would allow.
# origin: llm
# area: gradual_any
# hypothesis: Any propagates through attribute access and calls, while an object-typed value rejects attribute access that Any would allow.
# spec: typing spec, the Any type: Any is consistent with every type, and assert_type checks the exact inferred type.
from typing import Any, assert_type, cast, reveal_type


def untyped(x):
    return x


def takes_int(n: int) -> int:
    return n + 1


def bad_object(o: object) -> int:
    return o.bit_length()  # expect-error: object has no attribute bit_length


a: Any = 'hello'
b = a.upper()
reveal_type(b)  # Any
assert_type(b, Any)
c = takes_int(a)
reveal_type(c)  # int
assert_type(c, int)
d = untyped(3)
reveal_type(d)  # Any
assert_type(d, Any)
e: object = cast(Any, d)
reveal_type(e)  # object
assert_type(e, object)
print(b, c, d, e)
print(bad_object(3))
