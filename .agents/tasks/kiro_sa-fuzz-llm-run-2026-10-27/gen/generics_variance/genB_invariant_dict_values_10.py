from collections.abc import Mapping
from typing import reveal_type


class K1(str): ...


d: dict[str, int] = {"a": 1}
m1: Mapping[str, float] = d  # OK value covariant
m2: Mapping[object, int] = d  # error: key invariant
m3: dict[str, float] = d  # error
reveal_type(m1)
reveal_type(m2)
print(m1, m2, m3)
