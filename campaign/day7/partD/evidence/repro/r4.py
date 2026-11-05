class Desc:
    def deco(fn):
        return fn

    @deco
    def __get__(self, obj: object, owner: type | None = None) -> int:
        return 42


class Host:
    attr = Desc()


print(Desc.__get__(Desc(), None, Host))
