from typing import Self


class C:
    __call__: Self | None


x: C
x()
