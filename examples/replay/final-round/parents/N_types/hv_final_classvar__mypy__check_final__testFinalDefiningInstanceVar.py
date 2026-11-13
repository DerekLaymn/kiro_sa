# area: final_classvar
# origin: python/mypy check-final.test [case testFinalDefiningInstanceVar]
from typing import Final

class C:
    x: Final = int()
    y: Final[float] = int()
    z: Final[int] = int()
    bad: Final[str] = int()  # E: Incompatible types in assignment (expression has type "int", variable has type "str")
class D(C): pass

reveal_type(D.x)  # N: Revealed type is "builtins.int"
reveal_type(D.y)  # N: Revealed type is "builtins.float"
reveal_type(D.z)  # N: Revealed type is "builtins.int"
reveal_type(D().x)  # N: Revealed type is "builtins.int"
reveal_type(D().y)  # N: Revealed type is "builtins.float"
reveal_type(D().z)  # N: Revealed type is "builtins.int"
