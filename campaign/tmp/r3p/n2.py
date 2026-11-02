class A:
    def f(self, other: A) -> None:
        reveal_type(other)
