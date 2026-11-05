class Desc:
    def deco(fn):
        return fn

    @deco
    def __call__(self) -> int:
        return 42


Desc()()
