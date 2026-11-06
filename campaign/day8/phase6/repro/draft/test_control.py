from typing import overload


class Base:
    def post(self, value: int) -> None: ...


class Child(Base):
    @overload
    def post(self, value: int) -> None: ...
    @overload
    def post(self, value: str) -> None: ...
    def post(self, value: int | str) -> None:
        print(type(value))


Child().post(1)
