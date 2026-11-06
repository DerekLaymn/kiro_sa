class Shape:
    def scale(self, k: float) -> Shape:
        return self


print(Shape().scale(2.0))
