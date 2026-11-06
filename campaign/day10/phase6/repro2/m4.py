class K:
    def m(self, a: str, b: str, c: int) -> None: ...


K().m("x", 1)
K().m("x", "y")
