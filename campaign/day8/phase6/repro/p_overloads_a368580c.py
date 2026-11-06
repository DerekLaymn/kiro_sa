# area: overloads
# hypothesis: Overloads keyed on Literal and generic parameters should resolve to the first matching signature for both checkers, and CPython should return values matching that overload's declared type.
# origin: llm
# area: overloads
# hypothesis: Overloads keyed on Literal and generic arguments select the first matching signature, and the runtime values agree with the return type of the selected overload.
from typing import Literal, overload, reveal_type


@overload
def parse(kind: Literal['int'], value: str) -> int: ...
@overload
def parse(kind: Literal['float'], value: str) -> float: ...
@overload
def parse(kind: str, value: str) -> str: ...
def parse(kind: str, value: str) -> int | float | str:
    if kind == 'int':
        return int(value)
    if kind == 'float':
        return float(value)
    return value


@overload
def pick[T](kind: Literal['box'], value: T) -> list[T]: ...
@overload
def pick[T](kind: Literal['raw'], value: T) -> T: ...
def pick(kind: str, value: object) -> object:
    if kind == 'box':
        return [value]
    return value


a = parse('int', '7')
b = parse('float', '2.5')
k: str = 'int'
c = parse(k, '9')
reveal_type(a)
reveal_type(b)
reveal_type(c)
print(a, b, c)
print(pick('box', 3), pick('raw', 'x'))
reveal_type(pick('box', 3))
bad = parse('int', 5)  # expect-error: int is not str
print(bad)
