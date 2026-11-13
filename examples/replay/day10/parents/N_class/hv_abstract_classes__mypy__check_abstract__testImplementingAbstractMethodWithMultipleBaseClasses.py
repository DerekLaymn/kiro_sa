# area: abstract_classes
# origin: python/mypy check-abstract.test [case testImplementingAbstractMethodWithMultipleBaseClasses]
from abc import abstractmethod, ABCMeta
import typing
class I(metaclass=ABCMeta):
    @abstractmethod
    def f(self, x: int) -> int: pass
class J(metaclass=ABCMeta):
    @abstractmethod
    def g(self, x: str) -> str: pass
class A(I, J):
    def f(self, x: str) -> int: return 0 \
        # E: Argument 1 of "f" is incompatible with supertype "I"; supertype defines the argument type as "int" \
        # N: This violates the Liskov substitution principle \
        # N: See https://mypy.readthedocs.io/en/stable/common_issues.html#incompatible-overrides
    def g(self, x: str) -> int: return 0 \
        # E: Return type "int" of "g" incompatible with return type "str" in supertype "J"
    def h(self) -> int: return 0 # Not related to any base class
