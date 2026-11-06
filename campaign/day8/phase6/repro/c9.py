from typing import reveal_type


def wrap(fn):
    def inner(self, obj: object) -> None:
        fn(self, obj)

    return inner


class Desc:
    @wrap
    def run(self, obj: object) -> None:
        print("run")


reveal_type(wrap)
reveal_type(Desc.run)
reveal_type(Desc().run)
Desc.run(Desc(), 1, 2)
Desc().run(1, 2)
Desc().run()
