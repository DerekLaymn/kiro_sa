class Swallow:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: object) -> bool:
        return True


def f(fail: bool) -> str:
    with Swallow():
        if fail:
            raise TypeError("boom")
        result = "ok"
    return result


print(f(False))
try:
    print(f(True))
except UnboundLocalError as exc:
    print("UnboundLocalError:", exc)
