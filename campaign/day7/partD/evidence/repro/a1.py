from abc import ABC, abstractmethod


class Source(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...


class Fixed:
    @property
    def name(self) -> str:
        return "fixed"


class Other:
    @property
    def name(self) -> str:
        return "other"


Source.register(Fixed)


def load(src: Source) -> str:
    return src.name


print(load(Fixed()))  # runtime ok (virtual subclass)
print(load(Other()))  # no register: not a Source
