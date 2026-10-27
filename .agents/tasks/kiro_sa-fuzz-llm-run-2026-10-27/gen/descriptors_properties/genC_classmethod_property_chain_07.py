from typing import reveal_type


class Meta(type):
    @property
    def tag(cls) -> str:
        return cls.__name__.lower()


class K(metaclass=Meta):
    pass


reveal_type(K.tag)
print(K.tag)
try:
    print(K().tag)  # type: ignore
except AttributeError:
    print("AttributeError")
