class Desc:
    def deco(fn):
        return fn

    @deco
    def __get__(self, obj, owner=None):
        return 42


class Host:
    attr = Desc()


h = Host()
print(h.attr)
