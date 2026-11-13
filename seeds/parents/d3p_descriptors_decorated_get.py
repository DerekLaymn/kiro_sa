# area: descriptors_properties
# hypothesis: A decorator defined in the class body (no self) applied to __get__, then __get__ accessed on the class; descriptor lookup through a decorated dunder disagrees between checkers. Vary: decorate __set__, use a staticmethod/classmethod decorator, or return a descriptor from the decorator.
# origin: team-filed minimized repro
class C:
    def d() -> "C":
        pass

    @d
    def __get__():
        pass


C.__get__()
