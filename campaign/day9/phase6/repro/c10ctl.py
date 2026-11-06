class Strict:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: object) -> None:
        return None


def f(fail: bool) -> str:
    with Strict():
        if fail:
            raise TypeError("boom")
        result = "ok"
    return result


print(f(False))
try:
    print(f(True))
except TypeError as exc:
    print("TypeError (propagated):", exc)
