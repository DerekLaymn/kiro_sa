import asyncio
from typing import reveal_type


class Base:
    def get(self) -> int:
        return 1

    @staticmethod
    def util(x: int) -> int:
        return x


class Sub(Base):
    async def get(self) -> int:  # type: ignore
        return 2

    def util(self, x: int) -> int:  # type: ignore
        return x + 1


def call(b: Base) -> None:
    r = b.get()
    reveal_type(r)
    print(type(r).__name__)
    if asyncio.iscoroutine(r):
        r.close()


call(Base())
call(Sub())
try:
    print(Base.util(1), Sub.util(1))  # type: ignore
except TypeError:
    print("TypeError")
