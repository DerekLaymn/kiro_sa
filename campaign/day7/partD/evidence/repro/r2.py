class Desc:
    def deco(fn):
        return fn

    @deco
    def __set__(self, obj: object, value: int) -> None:
        print("set", value)


class Host:
    attr = Desc()


h = Host()
h.attr = 5
