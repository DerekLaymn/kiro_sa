class Desc:
    def wrap(fn):
        def inner(self, obj: object) -> None:
            fn(self, obj)

        return inner

    @wrap
    def run(self, obj: object) -> None:
        print("run")


d = Desc()
try:
    Desc.run(d, 1, 2)
except TypeError as exc:
    print("runtime:", type(exc).__name__)
