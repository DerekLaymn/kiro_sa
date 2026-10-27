from typing import reveal_type


class Producer[T]:
    def get(self) -> T:
        raise NotImplementedError


class IntProducer(Producer[int]):
    def get(self) -> int:
        return 1


def run(p: Producer[float]) -> float:
    return p.get()


reveal_type(IntProducer().get())
print(run(IntProducer()))  # Producer[T] infers covariant
