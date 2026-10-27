from typing import Any, Generic, TypeVar, overload, reveal_type

T = TypeVar("T")


class Field(Generic[T]):
    def __init__(self, default: T) -> None:
        self.default = default

    @overload
    def __get__(self, obj: None, owner: type) -> "Field[T]": ...
    @overload
    def __get__(self, obj: object, owner: type) -> T: ...
    def __get__(self, obj: object | None, owner: type) -> "Field[T] | T":
        if obj is None:
            return self
        return self.default


class Model:
    age = Field(3)
    label = Field("x")


m = Model()
reveal_type(m.age)
reveal_type(Model.age)
reveal_type(m.label)
reveal_type(Model.label.default)
print(m.age + 1, m.label.upper(), Model.age.default)
