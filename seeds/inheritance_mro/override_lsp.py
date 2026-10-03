# area: inheritance_mro
# hypothesis: method override compatibility (parameter contravariance, return covariance, keyword names,
# added required params), and super() in multiple inheritance.
# spec: typing spec, class-compat.html "Override compatibility".
class Animal:
    def feed(self, food: str, *, amount: int = 1) -> object:
        return food

    def speak(self) -> str:
        return "..."


class Dog(Animal):
    def feed(self, food: object, *, amount: int = 1) -> str:  # ok: wider param, narrower return
        return str(food)

    def speak(self, loud: bool) -> str:  # expect-error: added required parameter
        return "WOOF" if loud else "woof"


class Cat(Animal):
    def feed(self, meal: str, *, amount: int = 1) -> object:  # expect-error: renamed positional-or-keyword
        return meal


class A:
    def who(self) -> list[str]:
        return ["A"]


class B(A):
    def who(self) -> list[str]:
        return ["B", *super().who()]


class C(A):
    def who(self) -> list[str]:
        return ["C", *super().who()]


class D(B, C):
    def who(self) -> list[str]:
        return ["D", *super().who()]


print(Dog().feed(1), Cat().feed("fish"), D().who())
