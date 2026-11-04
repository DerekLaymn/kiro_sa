class C:
    def d() -> "C":
        pass

    @d
    def __get__():
        pass
