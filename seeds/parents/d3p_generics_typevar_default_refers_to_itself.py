# area: generics_variance
# hypothesis: A TypeVar whose default is a string naming itself, used as a Generic parameter; mypy crashes on the cyclic default. Vary: the default names another TypeVar, use PEP 695 `class C[T = T]`, use ParamSpec/TypeVarTuple defaults.
# origin: mypy crash reproduction
from typing import Generic, TypeVar

T = TypeVar("T", default="T")

class C(Generic[T]): ...
