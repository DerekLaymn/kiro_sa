class Desc:
    def deco(fn):
        return fn

    @deco
    def __get__(self, obj: object, owner: type | None = None) -> int:
        return 42


class Host:
    attr = Desc()


h = Host()
reveal_type(h.attr)
