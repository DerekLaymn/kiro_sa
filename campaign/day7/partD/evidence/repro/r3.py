class Plain:
    def deco(fn):
        return fn

    @deco
    def method(self) -> int:
        return 42


print(Plain().method())
