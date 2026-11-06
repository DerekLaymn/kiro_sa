from typing import reveal_type


def wrap(fn):
    def inner(self, obj: object) -> None:
        fn(self, obj)

    return inner


def plain(self, obj: object) -> None:
    print("plain")


class Desc:
    run = wrap(plain)

    @wrap
    def run2(self, obj: object) -> None:
        print("run")


reveal_type(wrap(plain))
reveal_type(Desc.run)
reveal_type(Desc().run2)
Desc().run(1, 2)
Desc().run2(1, 2)
