from typing import reveal_type


class Other:
    def __init__(self) -> None:
        self.tag = "other"


class K:
    def __new__(cls) -> Other:  # type: ignore
        return Other()

    def __init__(self) -> None:
        self.tag = "k"


k = K()
reveal_type(k)
print(k.tag, type(k).__name__)
