# area: gradual_any
# origin: python/mypy check-functions.test [case testTypeCheckBodyOfConditionalFunction]
from typing import Any
x = None # type: Any
if x:
    def f(x: int) -> None:
        if int():
            x = 1
            x = '' # E: Incompatible types in assignment (expression has type "str", variable has type "int")
